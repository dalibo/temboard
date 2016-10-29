import os
import json
import datetime
from datetime import timedelta

import tornado.web
import tornado.escape
from tornado.template import Loader

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import *

from temboardui.handlers.base import JsonHandler, BaseHandler, CsvHandler
from temboardui.plugins.supervision.model.orm import *
from temboardui.plugins.supervision.model.tables import *
from temboardui.plugins.supervision.chartdata import *
from temboardui.async import *
from temboardui.errors import TemboardUIError
from temboardui.application import get_instance
from temboardui.logger import get_tb

def configuration(config):
    return {}

def get_routes(config):
    plugin_path = os.path.dirname(os.path.realpath(__file__))
    handler_conf = {
        'ssl_ca_cert_file': config.temboard['ssl_ca_cert_file'],
        'template_path':  plugin_path + "/templates"
    }
    routes = [
        (r"/server/(.*)/([0-9]{1,5})/supervision/(day|week|month||year|interval)$", SupervisionHTMLHandler, handler_conf),
        (r"/supervision/collector", SupervisionCollectorHandler, handler_conf),
        (r"/server/(.*)/([0-9]{1,5})/supervision/data/([a-z\-_.0-9]{1,64})$", SupervisionDataProbeHandler, handler_conf),
        (r"/js/supervision/(.*)", tornado.web.StaticFileHandler, {'path': plugin_path + "/static/js"}),
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

def check_agent_key(session, hostname, pg_data, pg_port, agent_key):
    result = session.execute("SELECT agent_key FROM application.instances WHERE hostname = :hostname AND pg_data = :pgdata AND pg_port = :pgport LIMIT 1", {"hostname": hostname, "pgdata": pg_data, "pgport": pg_port})
    try:
        row = result.fetchone()
        if row[0] == agent_key:
            return
    except Exception as e:
        raise Exception("Can't find the instance \"%s\" in application.instances table." % hostname)
    raise Exception("Can't check agent's key.")

def check_host_key(session, hostname, agent_key):
    result = session.execute("SELECT agent_key FROM application.instances WHERE hostname = :hostname", {"hostname": hostname})
    try:
        for row in result.fetchall():
            if row[0] == agent_key:
                return
    except Exception as e:
        raise Exception("Can't find the instance \"%s\" in application.instances table." % hostname)
    raise Exception("Can't check agent's key.")

def insert_metrics(session, host, agent_data, logger, hostname):
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
            # Add hostname from hostinfo to each line
            line['hostname'] = hostname
        try:
            session.execute(table.insert().values(agent_data[metric]))
            session.flush()
            session.commit()
        except Exception as e:
            logger.info("Metric data not inserted in table '%s'" % (table.name))
            logger.debug(agent_data[metric])
            logger.traceback(get_tb())
            logger.error(str(e))
            session.rollback()

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
            return JSONAsyncResult(http_code = 401, data = {'error': 'X-Key header missing'})
        try:
            data = tornado.escape.json_decode(self.request.body)
            # Insert data in an other thread.
        except Exception as e:
            return JSONAsyncResult(http_code = 500, data = {'error': e.message})
        try:
            # We need to use a scoped_session object here as far the
            # code below is executed in its own thread.
            session_factory = sessionmaker(bind=self.engine)
            Session = scoped_session(session_factory)
            thread_session = Session()

            # Check the key
            if data['instances'][0]['available']:
                check_agent_key(thread_session, data['hostinfo']['hostname'], data['instances'][0]['data_directory'], data['instances'][0]['port'], key)
            else:
                # Case when PostgreSQL instance is not started.
                check_host_key(thread_session, data['hostinfo']['hostname'], key)
            # Update the inventory
            host = merge_agent_info(thread_session,
                    data['hostinfo'],
                    data['instances'])

            # Send the write SQL commands to the database because the
            # metrics are inserted with queries not the orm. Tables must
            # be there.
            thread_session.flush()
            thread_session.commit()

            # Insert metrics data
            insert_metrics(thread_session, host, data['data'], self.logger, data['hostinfo']['hostname'])
            # Close the session
            thread_session.close()
            return JSONAsyncResult(http_code = 200, data = {'done': True})
        except IntegrityError as e:
            self.logger.traceback(get_tb())
            self.logger.error(str(e))
            try:
                thread_session.rollback()
                thread_session.close()
            except Exception:
                pass
            return JSONAsyncResult(http_code = 409, data = {'error': e.message})
        except Exception as e:
            self.logger.traceback(get_tb())
            self.logger.error(str(e))
            try:
                thread_session.rollback()
                thread_session.close()
            except Exception:
                pass
            return JSONAsyncResult(http_code = 500, data = {'error': e.message})

    @tornado.web.asynchronous
    def post(self,):
        run_background(self.push_data, self.async_callback)


class SupervisionDataProbeHandler(CsvHandler):

    def get_data_probe(self, agent_address, agent_port, probe_name):
        try:
            instance = None
            role = None

            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            if not role:
                raise TemboardUIError(302, "Current role unknown.")

            instance = get_instance(self.db_session, agent_address, agent_port)
            if not instance:
                raise TemboardUIError(404, "Instance not found.")
            if __name__ not in [plugin.plugin_name for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")
            self.db_session.expunge_all()

            dbname = self.get_argument('dbname', default=None)
            start = self.get_argument('start', default=None)
            end = self.get_argument('end', default=None)
            start_time = None
            end_time = None
            if start:
                try:
                    start_time = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S')
                except ValueError as e:
                    raise TemboardUIError(406, 'Datetime not valid.')
            if end:
                try:
                    end_time = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S')
                except ValueError as e:
                    raise TemboardUIError(406, 'Datetime not valid.')

            if probe_name == 'loadavg':
                data = get_loadaverage(self.db_session, instance.hostname, start_time, end_time)
            elif probe_name == 'db_size':
                data = get_db_size(self.db_session, instance.hostname, instance.pg_port, start_time, end_time)
            elif probe_name == 'cpu':
                data = get_cpu(self.db_session, instance.hostname, start_time, end_time)
            elif probe_name == 'tps':
                data = get_tps(self.db_session, instance.hostname, instance.pg_port, start_time, end_time)
            elif probe_name == 'memory':
                data = get_memory(self.db_session, instance.hostname, start_time, end_time)
            elif probe_name == 'swap':
                data = get_swap(self.db_session, instance.hostname, start_time, end_time)
            elif probe_name == 'ctxforks':
                data = get_ctxforks(self.db_session, instance.hostname, start_time, end_time)
            elif probe_name == 'sessions':
                data = get_sessions(self.db_session, instance.hostname, instance.pg_port, start_time, end_time)
            elif probe_name == 'blocks':
                data = get_blocks(self.db_session, instance.hostname, instance.pg_port, start_time, end_time)
            elif probe_name == 'hitreadratio':
                data = get_hitreadratio(self.db_session, instance.hostname, instance.pg_port, start_time, end_time)
            elif probe_name == 'checkpoints':
                data = get_checkpoints(self.db_session, instance.hostname, instance.pg_port, start_time, end_time)
            elif probe_name == 'w_buffers':
                data = get_written_buffers(self.db_session, instance.hostname, instance.pg_port, start_time, end_time)
            elif probe_name == 'instance_size':
                data = get_instance_size(self.db_session, instance.hostname, instance.pg_port, start_time, end_time)
            elif probe_name == 'locks':
                data = get_locks(self.db_session, instance.hostname, instance.pg_port, start_time, end_time)
            elif probe_name == 'waiting_locks':
                data = get_waiting_locks(self.db_session, instance.hostname, instance.pg_port, start_time, end_time)
            elif probe_name == 'fs_size':
                data = get_fs_size(self.db_session, instance.hostname, start_time, end_time)
            elif probe_name == 'fs_usage':
                data = get_fs_usage(self.db_session, instance.hostname, start_time, end_time)
            elif probe_name == 'tblspc_size':
                data = get_tblspc_size(self.db_session, instance.hostname, instance.pg_port, start_time, end_time)
            elif probe_name == 'wal_files_size':
                data = get_wal_files_size(self.db_session, instance.hostname, instance.pg_port, start_time, end_time)
            elif probe_name == 'wal_files_count':
                data = get_wal_files_count(self.db_session, instance.hostname, instance.pg_port, start_time, end_time)
            elif probe_name == 'wal_files_rate':
                data = get_wal_files_rate(self.db_session, instance.hostname, instance.pg_port, start_time, end_time)
            else:
                raise TemboardUIError(404, 'Unknown probe.')

            self.db_session.commit()
            self.db_session.close()

            return CSVAsyncResult(http_code = 200, data = data)
        except (TemboardUIError, Exception) as e:
            self.logger.traceback(get_tb())
            self.logger.error(str(e))
            try:
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, TemboardUIError)):
                return CSVAsyncResult(http_code = e.code, data = {'error': e.message})
            else:
                return CSVAsyncResult(http_code = 500, data = {'error': e.message})

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port, probe_name):
        run_background(self.get_data_probe, self.async_callback, (agent_address, agent_port, probe_name))

class SupervisionHTMLHandler(BaseHandler):
    def get_index(self, agent_address, agent_port, period):
        try:
            instance = None
            role = None
            delta = None

            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            if not role:
                raise TemboardUIError(302, "Current role unknown.")

            instance = get_instance(self.db_session, agent_address, agent_port)
            if not instance:
                raise TemboardUIError(404, "Instance not found.")
            if __name__ not in [plugin.plugin_name for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()

            if period == 'day':
                delta = timedelta(hours=24)
            elif period == 'week':
                delta = timedelta(days=7)
            elif period == 'month':
                delta = timedelta(days=31)
            elif period == 'year':
                delta = timedelta(days=365)
            elif period == 'interval':
                start = self.get_argument('start', default=None)
                end = self.get_argument('end', default=None)
                try:
                    start_date = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S')
                    end_date = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S')
                except Exception as e:
                    raise TemboardUIError(406, 'Datetime not valid.')
            else:
                raise TemboardUIError(500, "Unknown period.")

            if period != 'interval':
                start_date = datetime.datetime.now() - delta
                end_date = datetime.datetime.now()
            return HTMLAsyncResult(
                    http_code = 200,
                    template_path = self.template_path,
                    template_file = 'index.html',
                    data = {
                        'nav': True,
                        'role': role,
                        'instance': instance,
                        'period': period,
                        'start_date': start_date.strftime('%Y-%m-%dT%H:%M:%S'),
                        'end_date': end_date.strftime('%Y-%m-%dT%H:%M:%S')
                    })

        except (TemboardUIError, Exception) as e:
            self.logger.traceback(get_tb())
            self.logger.error(str(e))
            try:
                self.db_session.expunge_all()
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, TemboardUIError)):
                if e.code == 302:
                    return HTMLAsyncResult(http_code = 401, redirection = "/login")
                code = e.code
            else:
                code = 500
            return HTMLAsyncResult(
                        http_code = code,
                        template_file = 'error.html',
                        data = {
                            'nav': True,
                            'role': role,
                            'instance': instance,
                            'code': e.code,
                            'error': e.message
                        })

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port, period):
        run_background(self.get_index, self.async_callback, (agent_address, agent_port, period))
