import logging
from dateutil import parser as dt_parser

import tornado.web
import tornado.escape

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import (
    IntegrityError,
)

from temboardui.scheduler import taskmanager
from temboardui.handlers.base import JsonHandler, BaseHandler, CsvHandler
from temboardui.temboardclient import TemboardError, temboard_profile
from temboardui.errors import TemboardUIError
from temboardui.async import (
    run_background,
    HTMLAsyncResult,
    JSONAsyncResult,
    CSVAsyncResult,
)

from ..chartdata import get_metric_data_csv
from ..tools import (
    check_agent_key,
    check_host_key,
    get_host_checks,
    get_host_id,
    get_instance_id,
    insert_metrics,
    merge_agent_info,
    populate_host_checks,
)
from ..alerting import check_specs


logger = logging.getLogger(__name__)


class MonitoringCollectorHandler(JsonHandler):

    @property
    def engine(self):
        return self.application.engine

    def push_data(self,):
        config = self.application.config
        key = self.request.headers.get('X-Key')
        if not key:
            return JSONAsyncResult(http_code=401,
                                   data={'error': 'X-Key header missing'})
        try:
            data = tornado.escape.json_decode(self.request.body)
            # Insert data in an other thread.
        except Exception as e:
            return JSONAsyncResult(http_code=500, data={'error': e.message})
        try:
            # We need to use a scoped_session object here as far the
            # code below is executed in its own thread.
            session_factory = sessionmaker(bind=self.engine)
            Session = scoped_session(session_factory)
            thread_session = Session()

            # Check the key
            if data['instances'][0]['available']:
                check_agent_key(thread_session,
                                data['hostinfo']['hostname'],
                                data['instances'][0]['data_directory'],
                                data['instances'][0]['port'],
                                key)
            else:
                # Case when PostgreSQL instance is not started.
                check_host_key(thread_session,
                               data['hostinfo']['hostname'],
                               key)
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
            insert_metrics(
                thread_session, host, data['data'], self.logger,
                data['hostinfo']['hostname'], data['instances'][0]['port'])

            # Alerting part
            host_id = get_host_id(thread_session, data['hostinfo']['hostname'])
            instance_id = get_instance_id(thread_session, host_id,
                                          data['instances'][0]['port'])
            # Populate host checks if needed
            populate_host_checks(thread_session, host_id, instance_id,
                                 dict(n_cpu=data['hostinfo']['cpu_count']))
            # Getting checks for this host/instance
            enabled_checks = get_host_checks(thread_session, host_id)
            thread_session.close()

            # Add max_connections value to data
            data['data']['max_connections'] = \
                data['instances'][0]['max_connections']

            task_options = dict(dbconf=config.repository,
                                host_id=host_id,
                                instance_id=instance_id,
                                data=list())
            specs = check_specs
            # Populate data with preprocessed values
            for check in enabled_checks:
                spec = specs.get(check[0])
                if not spec:
                    continue

                try:
                    v = spec.get('preprocess')(data['data'])
                except Exception as e:
                    logger.exception(e)
                    logger.warn("Not able to preprocess '%s' data." % check[0])
                    continue

                v = {'': v} if not type(v) is dict else v
                for key, val in v.items():
                    task_options['data'].append(dict(
                        datetime=data['datetime'],
                        name=check[0],
                        key=key,
                        value=val,
                        warning=check[1],
                        critical=check[2]))

            # Create new task for checking preprocessed values
            taskmanager.schedule_task(
                'check_data_worker',
                options=task_options,
                listener_addr=str(config.temboard['tm_sock_path']),
                expire=0,
            )

            return JSONAsyncResult(http_code=200, data={'done': True})
        except IntegrityError as e:
            self.logger.exception(str(e))
            try:
                thread_session.rollback()
                thread_session.close()
            except Exception:
                pass
            return JSONAsyncResult(http_code=409, data={'error': e.message})
        except Exception as e:
            self.logger.exception(str(e))
            try:
                thread_session.rollback()
                thread_session.close()
            except Exception:
                pass
            return JSONAsyncResult(http_code=500, data={'error': e.message})

    @tornado.web.asynchronous
    def post(self,):
        run_background(self.push_data, self.async_callback)


class MonitoringDataMetricHandler(CsvHandler):

    @CsvHandler.catch_errors
    def get_data_metric(self, agent_address, agent_port, metric_name):

        self.setUp(agent_address, agent_port)
        self.check_active_plugin('monitoring')

        # Find host_id & instance_id
        host_id = get_host_id(self.db_session, self.instance.hostname)
        instance_id = get_instance_id(self.db_session, host_id,
                                      self.instance.pg_port)

        start = self.get_argument('start', default=None)
        end = self.get_argument('end', default=None)
        key = self.get_argument('key', default=None)
        start_time = None
        end_time = None
        if start:
            try:
                start_time = dt_parser.parse(start)
            except ValueError as e:
                raise TemboardUIError(406, 'Datetime not valid.')
        if end:
            try:
                end_time = dt_parser.parse(end)
            except ValueError as e:
                raise TemboardUIError(406, 'Datetime not valid.')
        try:
            # Try to load data from the repository
            data = get_metric_data_csv(self.db_session, metric_name,
                                       start_time, end_time,
                                       host_id=host_id,
                                       instance_id=instance_id, key=key)
        except IndexError as e:
            logger.exception(str(e))
            raise TemboardUIError(404, 'Unknown metric.')

        return CSVAsyncResult(http_code=200, data=data)

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port, metric_name):
        run_background(self.get_data_metric, self.async_callback,
                       (agent_address, agent_port, metric_name))


class MonitoringHTMLHandler(BaseHandler):

    @BaseHandler.catch_errors
    def get_index(self, agent_address, agent_port):

        self.setUp(agent_address, agent_port)
        self.check_active_plugin('monitoring')

        xsession = self.get_secure_cookie(
            "temboard_%s_%s" % (agent_address, agent_port))

        # Here we want to get the current agent username if a session
        # already exists.
        # Monitoring plugin doesn't require agent authentication since we
        # already have the data.
        # Don't fail if there's a session error (for example when the agent
        # has been restarted)
        agent_username = None
        try:
            if xsession:
                data_profile = temboard_profile(self.ssl_ca_cert_file,
                                                agent_address,
                                                agent_port,
                                                xsession)
                agent_username = data_profile['username']
        except TemboardError:
            pass

        return HTMLAsyncResult(
                http_code=200,
                template_path=self.template_path,
                template_file='index.html',
                data={
                    'nav': True,
                    'role': self.current_user,
                    'instance': self.instance,
                    'plugin': 'monitoring',
                    'agent_username': agent_username
                })

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_index, self.async_callback,
                       (agent_address, agent_port))
