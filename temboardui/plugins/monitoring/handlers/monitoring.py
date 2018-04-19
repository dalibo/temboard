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
from temboardui.application import get_instance
from temboardui.async import (
    run_background,
    HTMLAsyncResult,
    JSONAsyncResult,
    CSVAsyncResult,
)

from ..chartdata import (
    get_blocks,
    get_checkpoints,
    get_cpu,
    get_ctxforks,
    get_db_size,
    get_fs_size,
    get_fs_usage,
    get_hitreadratio,
    get_instance_size,
    get_loadaverage,
    get_locks,
    get_memory,
    get_sessions,
    get_swap,
    get_tblspc_size,
    get_tps,
    get_waiting_locks,
    get_wal_files_count,
    get_wal_files_rate,
    get_wal_files_size,
    get_written_buffers,
)

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


class MonitoringDataProbeHandler(CsvHandler):

    def get_data_probe(self, agent_address, agent_port, probe_name):
        try:
            instance = None
            role = None
            no_error = 0

            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            if not role:
                raise TemboardUIError(302, "Current role unknown.")

            instance = get_instance(self.db_session, agent_address, agent_port)
            if not instance:
                raise TemboardUIError(404, "Instance not found.")
            if 'monitoring' not in [plugin.plugin_name
                                    for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")

            # Find host_id & instance_id
            host_id = get_host_id(self.db_session, instance.hostname)
            instance_id = get_instance_id(self.db_session, host_id,
                                          instance.pg_port)

            self.db_session.expunge_all()

            start = self.get_argument('start', default=None)
            end = self.get_argument('end', default=None)
            # Return 200 with empty list when an error occurs
            no_error = int(self.get_argument('noerror', default=0))
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

            if probe_name == 'loadavg':
                interval = self.get_argument('interval', default='all')
                if interval not in ['load1', 'load5', 'load15', 'all']:
                    raise TemboardUIError(400, 'Interval not available')
                data = get_loadaverage(
                    self.db_session, host_id, start_time, end_time, interval)
            elif probe_name == 'db_size':
                data = get_db_size(
                    self.db_session, instance_id, start_time, end_time)
            elif probe_name == 'cpu':
                data = get_cpu(
                    self.db_session, host_id, start_time, end_time)
            elif probe_name == 'tps':
                data = get_tps(
                    self.db_session, instance_id, start_time, end_time)
            elif probe_name == 'memory':
                data = get_memory(
                    self.db_session, host_id, start_time, end_time)
            elif probe_name == 'swap':
                data = get_swap(
                    self.db_session, host_id, start_time, end_time)
            elif probe_name == 'ctxforks':
                data = get_ctxforks(
                    self.db_session, host_id, start_time, end_time)
            elif probe_name == 'sessions':
                data = get_sessions(
                    self.db_session, instance_id, start_time, end_time)
            elif probe_name == 'blocks':
                data = get_blocks(
                    self.db_session, instance_id, start_time, end_time)
            elif probe_name == 'hitreadratio':
                data = get_hitreadratio(
                    self.db_session, instance_id, start_time, end_time)
            elif probe_name == 'checkpoints':
                data = get_checkpoints(
                    self.db_session, instance_id, start_time, end_time)
            elif probe_name == 'w_buffers':
                data = get_written_buffers(
                    self.db_session, host_id, start_time, end_time)
            elif probe_name == 'instance_size':
                data = get_instance_size(
                    self.db_session, instance_id, start_time, end_time)
            elif probe_name == 'locks':
                data = get_locks(
                    self.db_session, instance_id, start_time, end_time)
            elif probe_name == 'waiting_locks':
                data = get_waiting_locks(
                    self.db_session, instance_id, start_time, end_time)
            elif probe_name == 'fs_size':
                data = get_fs_size(
                    self.db_session, host_id, start_time, end_time)
            elif probe_name == 'fs_usage':
                data = get_fs_usage(
                    self.db_session, host_id, start_time, end_time)
            elif probe_name == 'tblspc_size':
                data = get_tblspc_size(
                    self.db_session, instance_id, start_time, end_time)
            elif probe_name == 'wal_files_size':
                data = get_wal_files_size(
                    self.db_session, instance_id, start_time, end_time)
            elif probe_name == 'wal_files_count':
                data = get_wal_files_count(
                    self.db_session, instance_id, start_time, end_time)
            elif probe_name == 'wal_files_rate':
                data = get_wal_files_rate(
                    self.db_session, instance_id, start_time, end_time)
            else:
                raise TemboardUIError(404, 'Unknown probe.')

            self.db_session.commit()
            self.db_session.close()

            return CSVAsyncResult(http_code=200, data=data)
        except (TemboardUIError, Exception) as e:
            self.logger.exception(str(e))
            try:
                self.db_session.close()
            except Exception:
                pass
            if no_error == 1:
                return CSVAsyncResult(http_code=200, data=u'')
            else:
                if (isinstance(e, TemboardUIError)):
                    return CSVAsyncResult(http_code=e.code,
                                          data={'error': e.message})
                else:
                    return CSVAsyncResult(http_code=500,
                                          data={'error': e.message})

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port, probe_name):
        run_background(self.get_data_probe, self.async_callback,
                       (agent_address, agent_port, probe_name))


class MonitoringHTMLHandler(BaseHandler):
    def get_index(self, agent_address, agent_port):
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
            if 'monitoring' not in [plugin.plugin_name
                                    for plugin in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")
            self.db_session.expunge_all()
            self.db_session.commit()
            self.db_session.close()

            xsession = self.get_secure_cookie(
                "temboard_%s_%s" %
                (instance.agent_address, instance.agent_port))

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
                                                    instance.agent_address,
                                                    instance.agent_port,
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
                        'role': role,
                        'instance': instance,
                        'plugin': 'monitoring',
                        'agent_username': agent_username
                    })

        except (TemboardUIError, Exception) as e:
            self.logger.exception(str(e))
            try:
                self.db_session.expunge_all()
                self.db_session.rollback()
                self.db_session.close()
            except Exception:
                pass
            if (isinstance(e, TemboardUIError)):
                if e.code == 302:
                    return HTMLAsyncResult(http_code=401, redirection="/login")
                code = e.code
            else:
                code = 500
            return HTMLAsyncResult(
                        http_code=code,
                        template_file='error.html',
                        data={
                            'nav': True,
                            'role': role,
                            'instance': instance,
                            'code': e.code,
                            'error': e.message
                        })

    @tornado.web.asynchronous
    def get(self, agent_address, agent_port):
        run_background(self.get_index, self.async_callback,
                       (agent_address, agent_port))
