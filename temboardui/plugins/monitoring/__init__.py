import logging
import os
import dateutil
import time

import tornado.web
import tornado.escape

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import (
    IntegrityError,
)
from sqlalchemy import create_engine
from sqlalchemy.schema import (
    MetaData,
)

from temboardui.handlers.base import JsonHandler, BaseHandler, CsvHandler
from temboardui.plugins.monitoring.model.orm import (
    Host,
    Instance,
)
from temboardui.plugins.monitoring.chartdata import (
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
from temboardui.async import (
    run_background,
    HTMLAsyncResult,
    JSONAsyncResult,
    CSVAsyncResult,
)
from temboardui.temboardclient import (
    TemboardError,
    temboard_profile,
)
from temboardui.configuration import Configuration
from temboardui.errors import TemboardUIError, ConfigurationError
from temboardui.application import get_instance
from temboardui.taskmanager import (
    add_worker,
    add_scheduler,
    Task,
    S_TASK_TODO,
    serialize_task_parameters,
    unserialize_task_parameters
)


def configuration(config):
    return {}


def get_routes(config):
    plugin_path = os.path.dirname(os.path.realpath(__file__))
    handler_conf = {
        'ssl_ca_cert_file': config.temboard['ssl_ca_cert_file'],
        'template_path':  plugin_path + "/templates"
    }
    routes = [
        (r"/server/(.*)/([0-9]{1,5})/monitoring",
         MonitoringHTMLHandler,
         handler_conf),
        (r"/monitoring/collector", MonitoringCollectorHandler, handler_conf),
        # for compatibility with older agents keep an eye on requests on
        # supervision routes
        (r"/supervision/collector", MonitoringCollectorHandler, handler_conf),
        (r"/server/(.*)/([0-9]{1,5})/monitoring/data/([a-z\-_.0-9]{1,64})$",
         MonitoringDataProbeHandler, handler_conf),
        (r"/js/monitoring/(.*)", tornado.web.StaticFileHandler,
         {'path': plugin_path + "/static/js"}),
    ]
    return routes


def bind_metadata(engine):
    MetaData.bind = engine


def merge_agent_info(session, host_info, instances_info):
    """Update the host, instance and database information with the
    data received from the agent."""

    try:
        # Try to get host_id, based on hostname
        host_info['host_id'] = get_host_id(session, host_info['hostname'])
    except Exception:
        # host not found
        pass

    host = Host.from_dict(host_info)

    # Insert or update host information
    session.merge(host)
    session.flush()
    session.commit()

    # Get host_id in any case
    host_id = get_host_id(session, host_info['hostname'])

    for instance_info in instances_info:
        # Only process instances marked as available, since only those
        # have complete information
        if instance_info['available']:
            try:
                # Try to get instance_id
                instance_info['instance_id'] = get_instance_id(
                    session, host_id, instance_info['port']
                )
            except Exception:
                # instance not found
                pass
            instance_info['host_id'] = host_id

            inst = Instance.from_dict(instance_info)
            # Insert or update instance information
            session.merge(inst)
            session.flush()
            session.commit()
    return host


def get_host_id(session, hostname):
    """
    Get host_id from the hostname.
    """
    query = """
        SELECT host_id FROM monitoring.hosts
        WHERE hostname = :hostname
    """
    result = session.execute(query, {"hostname": hostname})
    try:
        return result.fetchone()[0]
    except Exception:
        raise Exception("Can't find host_id for \"%s\""
                        " in monitoring.hosts table." % hostname)


def get_instance_id(session, host_id, port):
    """
    Get instance from host_id and port.
    """
    query = """
        SELECT instance_id
        FROM monitoring.instances
        WHERE host_id = :host_id AND port = :port
    """
    result = session.execute(query, {"host_id": host_id, "port": port})
    try:
        return result.fetchone()[0]
    except Exception:
        raise Exception("Can't find instance_id for \"%s/%s\" "
                        "in monitoring.instances table." % (host_id, port))


def check_agent_key(session, hostname, pg_data, pg_port, agent_key):
    query = """
        SELECT agent_key
        FROM application.instances
        WHERE hostname = :hostname AND pg_data=:pgdata AND pg_port = :pgport
        LIMIT 1
    """
    result = session.execute(
        query,
        {"hostname": hostname, "pgdata": pg_data, "pgport": pg_port})
    try:
        row = result.fetchone()
        if row[0] == agent_key:
            return
    except Exception:
        raise Exception("Can't find the instance \"%s\" "
                        "in application.instances table." % hostname)
    raise Exception("Can't check agent's key.")


def check_host_key(session, hostname, agent_key):
    query = """
        SELECT agent_key
        FROM application.instances
        WHERE hostname = :hostname
    """
    result = session.execute(query, {"hostname": hostname})
    try:
        for row in result.fetchall():
            if row[0] == agent_key:
                return
    except Exception:
        raise Exception("Can't find the instance \"%s\" "
                        "in application.instances table." % hostname)
    raise Exception("Can't check agent's key.")


def insert_metrics(session, host, agent_data, logger, hostname, port):
    try:
        # Find host_id & instance_id
        host_id = get_host_id(session, hostname)
        instance_id = get_instance_id(session, host_id, port)
    except Exception as e:
        logger.info("Unable to find host & instance IDs")
        logger.debug(agent_data)
        logger.exception(str(e))
        session.rollback()
        return

    cur = session.connection().connection.cursor()
    for metric in agent_data.keys():
        # Do not try to insert empty lines
        if len(agent_data[metric]) == 0:
            continue

        try:
            # Insert data
            if metric == 'sessions':
                for metric_data in agent_data['sessions']:
                    query = """
                        INSERT INTO monitoring.metric_sessions_current
                        VALUES (%s, %s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            instance_id,
                            metric_data['dbname'],
                            (
                                None,
                                metric_data['active'],
                                metric_data['waiting'],
                                metric_data['idle'],
                                metric_data['idle_in_xact'],
                                metric_data['idle_in_xact_aborted'],
                                metric_data['fastpath'],
                                metric_data['disabled'],
                                metric_data['no_priv']
                            )
                        )
                    )

            elif metric == 'xacts':
                for metric_data in agent_data['xacts']:
                    query = """
                        INSERT INTO monitoring.metric_xacts_current
                        VALUES (%s, %s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            instance_id,
                            metric_data['dbname'],
                            (
                                None,
                                str(metric_data['measure_interval']),
                                metric_data['n_commit'],
                                metric_data['n_rollback']
                            )
                        )
                    )
            elif metric == 'locks':
                for metric_data in agent_data['locks']:
                    query = """
                        INSERT INTO monitoring.metric_locks_current
                        VALUES (%s, %s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            instance_id,
                            metric_data['dbname'],
                            (
                                None,
                                metric_data['access_share'],
                                metric_data['row_share'],
                                metric_data['row_exclusive'],
                                metric_data['share_update_exclusive'],
                                metric_data['share'],
                                metric_data['share_row_exclusive'],
                                metric_data['exclusive'],
                                metric_data['access_exclusive'],
                                metric_data['siread'],
                                metric_data['waiting_access_share'],
                                metric_data['waiting_row_share'],
                                metric_data['waiting_row_exclusive'],
                                metric_data['waiting_share_update_exclusive'],
                                metric_data['waiting_share'],
                                metric_data['waiting_share_row_exclusive'],
                                metric_data['waiting_exclusive'],
                                metric_data['waiting_access_exclusive']
                            )
                        )
                    )
            elif metric == 'blocks':
                for metric_data in agent_data['blocks']:
                    query = """
                        INSERT INTO monitoring.metric_blocks_current
                        VALUES (%s, %s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            instance_id,
                            metric_data['dbname'],
                            (
                                None,
                                str(metric_data['measure_interval']),
                                metric_data['blks_read'],
                                metric_data['blks_hit'],
                                metric_data['hitmiss_ratio']
                            )
                        )
                    )
            elif metric == 'bgwriter':
                for metric_data in agent_data['bgwriter']:
                    query = """
                        INSERT INTO monitoring.metric_bgwriter_current
                        VALUES (%s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            instance_id,
                            (
                                None,
                                str(metric_data['measure_interval']),
                                metric_data['checkpoints_timed'],
                                metric_data['checkpoints_req'],
                                metric_data['checkpoint_write_time'],
                                metric_data['checkpoint_sync_time'],
                                metric_data['buffers_checkpoint'],
                                metric_data['buffers_clean'],
                                metric_data['maxwritten_clean'],
                                metric_data['buffers_backend'],
                                metric_data['buffers_backend_fsync'],
                                metric_data['buffers_alloc'],
                                metric_data['stats_reset']
                            )
                        )
                    )
            elif metric == 'db_size':
                for metric_data in agent_data['db_size']:
                    query = """
                        INSERT INTO monitoring.metric_db_size_current
                        VALUES (%s, %s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            instance_id,
                            metric_data['dbname'],
                            (
                                None,
                                metric_data['size']
                            )
                        )
                    )
            elif metric == 'tblspc_size':
                for metric_data in agent_data['tblspc_size']:
                    query = """
                        INSERT INTO monitoring.metric_tblspc_size_current
                        VALUES (%s, %s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            instance_id,
                            metric_data['spcname'],
                            (
                                None,
                                metric_data['size']
                            )
                        )
                    )
            elif metric == 'filesystems_size':
                for metric_data in agent_data['filesystems_size']:
                    query = """
                        INSERT INTO monitoring.metric_filesystems_size_current
                        VALUES (%s, %s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            host_id,
                            metric_data['mount_point'],
                            (
                                None,
                                metric_data['used'],
                                metric_data['total'],
                                metric_data['device']
                            )
                        )
                    )
            elif metric == 'temp_files_size_tblspc':
                for metric_data in agent_data['temp_files_size_tblspc']:
                    query = """
                        INSERT INTO
                            monitoring.metric_temp_files_size_tblspc_current
                        VALUES (%s, %s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            instance_id,
                            metric_data['spcname'],
                            (
                                None,
                                metric_data['size']
                            )
                        )
                    )
            elif metric == 'temp_files_size_db':
                for metric_data in agent_data['temp_files_size_db']:
                    query = """
                        INSERT INTO
                            monitoring.metric_temp_files_size_db_current
                        VALUES (%s, %s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            instance_id,
                            metric_data['dbname'],
                            (
                                None,
                                metric_data['size']
                            )
                        )
                    )
            elif metric == 'wal_files':
                for metric_data in agent_data['wal_files']:
                    query = """
                        INSERT INTO monitoring.metric_wal_files_current
                        VALUES (%s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            instance_id,
                            (
                                None,
                                str(metric_data['measure_interval']),
                                metric_data['written_size'],
                                metric_data['current_location'],
                                metric_data['total'],
                                metric_data['archive_ready'],
                                metric_data['total_size']
                            )
                        )
                    )
            elif metric == 'cpu':
                for metric_data in agent_data['cpu']:
                    query = """
                        INSERT INTO monitoring.metric_cpu_current
                        VALUES (%s, %s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            host_id,
                            metric_data['cpu'],
                            (
                                None,
                                str(metric_data['measure_interval']),
                                metric_data['time_user'],
                                metric_data['time_system'],
                                metric_data['time_idle'],
                                metric_data['time_iowait'],
                                metric_data['time_steal']
                            )
                        )
                    )
            elif metric == 'process':
                for metric_data in agent_data['process']:
                    query = """
                        INSERT INTO monitoring.metric_process_current
                        VALUES (%s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            host_id,
                            (
                                None,
                                str(metric_data['measure_interval']),
                                metric_data['context_switches'],
                                metric_data['forks'],
                                metric_data['procs_running'],
                                metric_data['procs_blocked'],
                                metric_data['procs_total']
                            )
                        )
                    )
            elif metric == 'memory':
                for metric_data in agent_data['memory']:
                    query = """
                        INSERT INTO monitoring.metric_memory_current
                        VALUES (%s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            host_id,
                            (
                                None,
                                metric_data['mem_total'],
                                metric_data['mem_used'],
                                metric_data['mem_free'],
                                metric_data['mem_buffers'],
                                metric_data['mem_cached'],
                                metric_data['swap_total'],
                                metric_data['swap_used']
                            )
                        )
                    )
            elif metric == 'loadavg':
                for metric_data in agent_data['loadavg']:
                    query = """
                        INSERT INTO monitoring.metric_loadavg_current
                        VALUES (%s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            host_id,
                            (
                                None,
                                metric_data['load1'],
                                metric_data['load5'],
                                metric_data['load15']
                            )
                        )
                    )
            elif metric == 'vacuum_analyze':
                for metric_data in agent_data['vacuum_analyze']:
                    query = """
                        INSERT INTO monitoring.metric_vacuum_analyze_current
                        VALUES (%s, %s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            instance_id,
                            metric_data['dbname'],
                            (
                                None,
                                str(metric_data['measure_interval']),
                                metric_data['n_vacuum'],
                                metric_data['n_analyze'],
                                metric_data['n_autovacuum'],
                                metric_data['n_autoanalyze']
                            )
                        )
                    )
            elif metric == 'replication':
                for metric_data in agent_data['replication']:
                    query = """
                        INSERT INTO monitoring.metric_replication_current
                        VALUES (%s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            instance_id,
                            (
                                None,
                                metric_data['receive_location'],
                                metric_data['replay_location']
                            )
                        )
                    )

            session.connection().connection.commit()
        except Exception as e:
            logger.info("Metric data not inserted for '%s' type" % (metric))
            logger.debug(agent_data[metric])
            logger.exception(str(e))
            session.connection().connection.rollback()


class MonitoringCollectorHandler(JsonHandler):

    @property
    def engine(self):
        return self.application.engine

    def push_data(self,):
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

            # Close the session
            thread_session.close()
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

            self.load_auth_cookie()
            self.start_db_session()

            role = self.current_user
            if not role:
                raise TemboardUIError(302, "Current role unknown.")

            instance = get_instance(self.db_session, agent_address, agent_port)
            if not instance:
                raise TemboardUIError(404, "Instance not found.")
            if __name__ not in [plugin.plugin_name for plugin
                                in instance.plugins]:
                raise TemboardUIError(408, "Plugin not active.")

            # Find host_id & instance_id
            host_id = get_host_id(self.db_session, instance.hostname)
            instance_id = get_instance_id(self.db_session, host_id,
                                          instance.pg_port)

            self.db_session.expunge_all()

            start = self.get_argument('start', default=None)
            end = self.get_argument('end', default=None)
            start_time = None
            end_time = None
            if start:
                try:
                    start_time = dateutil.parser.parse(start)
                except ValueError as e:
                    raise TemboardUIError(406, 'Datetime not valid.')
            if end:
                try:
                    end_time = dateutil.parser.parse(end)
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
            if __name__ not in [plugin.plugin_name for plugin
                                in instance.plugins]:
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


@add_worker('worker_agg_data', 1)
def worker_data_agg(task):
    # Worker in charge of aggregate data
    logger = logging.getLogger("worker_agg_data")
    try:
        parameters = unserialize_task_parameters(task.parameters)
        config = Configuration(parameters['configpath'])
        dburi = 'postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
                    user=config.repository['user'],
                    password=config.repository['password'],
                    host=config.repository['host'],
                    port=config.repository['port'],
                    dbname=config.repository['dbname'])
        engine = create_engine(dburi)
        with engine.connect() as conn:
            conn.execute("SET search_path TO monitoring")
            res = conn.execute("SELECT * FROM aggregate_data()")
            for row in res.fetchall():
                logger.debug("table=%s insert=%s" %
                             (row['tblname'], row['nb_rows']))
            conn.execute("COMMIT")
            exit(0)
    except (ConfigurationError, ImportError, Exception) as e:
        try:
            logger.error.exception(str(e))
            try:
                conn.execute("ROLLBACK")
            except Exception as e:
                pass
        except Exception:
            pass
        exit(1)


@add_worker('worker_history_data', 1)
def worker_history_data(task):
    # Worker in charge of history data
    logger = logging.getLogger("worker_history_data")
    try:
        parameters = unserialize_task_parameters(task.parameters)
        config = Configuration(parameters['configpath'])
        dburi = 'postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
                    user=config.repository['user'],
                    password=config.repository['password'],
                    host=config.repository['host'],
                    port=config.repository['port'],
                    dbname=config.repository['dbname'])
        engine = create_engine(dburi)
        with engine.connect() as conn:
            conn.execute("SET search_path TO monitoring")
            res = conn.execute("SELECT * FROM history_tables()")
            for row in res.fetchall():
                logger.debug("table=%s insert=%s" %
                             (row['tblname'], row['nb_rows']))
            conn.execute("COMMIT")
            exit(0)
    except (ConfigurationError, ImportError, Exception) as e:
        try:
            logger.exception(str(e))
            try:
                conn.execute("ROLLBACK")
            except Exception as e:
                pass
        except Exception:
            pass
        exit(1)


@add_scheduler('scheduler_agg_data')
def scheduler_data_agg(task_list, parameters):
    task = Task(
            worker_name=b'worker_agg_data',
            taskid=b'task_agg_data',
            parameters=serialize_task_parameters(parameters),
            state=S_TASK_TODO,
            repeat=30 * 60,  # Repeat each 30min
            creation_time=int(time.time()))
    task_list.add(task)
    task_list.save()


@add_scheduler('scheduler_history_data')
def scheduler_history_data(task_list, parameters):
    task = Task(
            worker_name=b'worker_history_data',
            taskid=b'task_history_data',
            parameters=serialize_task_parameters(parameters),
            state=S_TASK_TODO,
            repeat=3 * 60 * 60,  # Repeat each 3h
            creation_time=int(time.time()))
    task_list.add(task)
    task_list.save()
