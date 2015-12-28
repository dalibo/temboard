import os
import json

import tornado.web
import tornado.escape
from tornado.template import Loader

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import *

from ganeshwebui.handlers.base import JsonHandler, BaseHandler
from ganeshwebui.plugins.supervision.model.orm import *
from ganeshwebui.plugins.supervision.model.tables import *
from ganeshwebui.async import *

def configuration(config):
    return {}

def get_routes(config):
    plugin_path = os.path.dirname(os.path.realpath(__file__))
    handler_conf = {
        'ssl_ca_cert_file': config.ganesh['ssl_ca_cert_file'],
        'template_path':  plugin_path + "/templates"
    }
    routes = [
        (r"/supervision/collector", SupervisionCollectorHandler, handler_conf),
    ]
    return routes


def bind_metadata(engine):
    MetaData.bind = engine

def merge_agent_info(session, host_info, instances_info):
    """Update the host, instance and database information with the
    data received from the agent."""

    host = Host.from_dict(host_info)

    # Insert or update host information
    session.merge(host)
    for instance_info in instances_info:
        # Only process instances marked as available, since only those
        # have complete information
        if instance_info['available']:
            inst = Instance.from_dict(instance_info)
            session.merge(inst)
    return host

def insert_metrics(session, host, agent_data):
    for metric in agent_data.keys():
        # Do not try to insert empty lines
        if len(agent_data[metric]) == 0:
            continue

        # Find the name to the Table object
        if 'metric_' + metric in globals().keys():
            table = globals()['metric_' + metric]
        else:
            continue

        # XXX The interval input must be a string to be cast by
        # PostgreSQL. It is used by the measure_interval value, which
        # come as a number
        for line in agent_data[metric]:
            if 'measure_interval' in line:
                line['measure_interval'] = str(line['measure_interval'])

        session.execute(table.insert().values(agent_data[metric]))

class SupervisionCollectorHandler(JsonHandler):
    def __init__(self, application, request, **kwargs):
        super(SupervisionCollectorHandler, self).__init__(
            application, request, **kwargs)
        self._session = None

    @property
    def engine(self):
        return self.application.engine

    def push_data(self,):
        key = self.request.headers.get('X-Key')
        if not key:
            return JSONAsyncResult(http_code = 401, data = {'error': 'X-Session header missing'})
        try:
            data = tornado.escape.json_decode(self.request.body)
            data['instances'][0]['agent_key'] = key
            # Insert data in an other thread.
        except Exception as e:
            return JSONAsyncResult(http_code = 500, data = {'error': e.message})
        try:
            # We need to use a scoped_session object here as far the
            # code below is executed in its own thread.
            session_factory = sessionmaker(bind=self.engine)
            Session = scoped_session(session_factory)
            thread_session = Session()

            # Update the inventory
            host = merge_agent_info(thread_session,
                    data['hostinfo'],
                    data['instances'])

            # Send the write SQL commands to the database because the
            # metrics are inserted with queries not the orm. Tables must
            # be there.
            thread_session.flush()

            # Insert metrics data
            insert_metrics(thread_session, host, data['data'])
            thread_session.commit()
            thread_session.close()
            return JSONAsyncResult(http_code = 200, data = {'done': True})
        except IntegrityError as e:
            try:
                thread_session.rollback()
                thread_session.close()
            except Exception:
                pass
            return JSONAsyncResult(http_code = 409, data = {'error': e.message})
        except Exception as e:
            try:
                thread_session.rollback()
                thread_session.close()
            except Exception:
                pass
            return JSONAsyncResult(http_code = 500, data = {'error': e.message})

    @tornado.web.asynchronous
    def post(self,):
        run_background(self.push_data, self.async_callback)
