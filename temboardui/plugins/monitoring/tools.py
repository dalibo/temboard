import logging
from dateutil import parser as parse_datetime

from temboardui.web import HTTPError

from .model.orm import (
    Check,
    Host,
    Instance,
)
from .alerting import (
    bootstrap_checks,
    check_specs,
)


logger = logging.getLogger(__name__)


def merge_agent_info(session, host_info, instance_info):
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


def get_request_ids(request):
    host_id = get_host_id(request.db_session, request.instance.hostname)
    instance_id = get_instance_id(
        request.db_session, host_id, request.instance.pg_port)
    return host_id, instance_id


def parse_start_end(request):
    start = request.handler.get_argument('start', default=None)
    end = request.handler.get_argument('end', default=None)
    try:
        if start:
            start = parse_datetime.parse(start)
        if end:
            end = parse_datetime.parse(end)
    except ValueError:
        raise HTTPError(406, 'Datetime not valid.')

    return start, end


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


def insert_availability(session, host, agent_data, logger, hostname, port):
    try:
        # Find host_id & instance_id
        host_id = get_host_id(session, hostname)
        instance_id = get_instance_id(session, host_id, port)
    except Exception as e:
        logger.info("Unable to find host & instance IDs")
        logger.exception(str(e))
        session.rollback()
        return

    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    try:
        query = """
            SELECT insert_instance_availability(%s, %s, %s)
        """
        cur.execute(
            query,
            (
                agent_data['datetime'],
                instance_id,
                agent_data['instances'][0]['available']
            )
        )
        cur.close()
    except Exception as e:
        logger.info("Availability data not inserted")
        logger.exception(str(e))
        session.connection().connection.rollback()


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
        if agent_data[metric] is None:
            continue
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
            elif metric == 'temp_files_size_delta':
                for metric_data in agent_data['temp_files_size_delta']:
                    query = """
                        INSERT INTO monitoring.metric_temp_files_size_delta_current
                        VALUES (%s, %s, %s, %s)
                    """  # noqa
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            instance_id,
                            metric_data['dbname'],
                            (
                                None,
                                str(metric_data['measure_interval']),
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
            elif metric == 'replication_lag':
                for metric_data in agent_data['replication_lag']:
                    query = """
                        INSERT INTO monitoring.metric_replication_lag_current
                        VALUES (%s, %s, %s)
                    """
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            instance_id,
                            (
                                None,
                                metric_data['lag']
                            )
                        )
                    )
            elif metric == 'replication_connection':
                for metric_data in agent_data['replication_connection']:
                    query = """
                        INSERT INTO monitoring.metric_replication_connection_current
                        VALUES (%s, %s, %s, %s)
                    """  # noqa
                    cur.execute(
                        query,
                        (
                            metric_data['datetime'],
                            instance_id,
                            metric_data['upstream'],
                            (
                                None,
                                metric_data['connected']
                            )
                        )
                    )
            elif metric == 'heap_bloat':
                for metric_data in agent_data['heap_bloat']:
                    query = """
                        INSERT INTO monitoring.metric_heap_bloat_current
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
                                metric_data['ratio']
                            )
                        )
                    )
            elif metric == 'btree_bloat':
                for metric_data in agent_data['btree_bloat']:
                    query = """
                        INSERT INTO monitoring.metric_btree_bloat_current
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
                                metric_data['ratio']
                            )
                        )
                    )

            session.connection().connection.commit()
        except Exception as e:
            logger.info("Metric data not inserted for '%s' type" % (metric))
            logger.debug(agent_data[metric])
            logger.exception(str(e))
            session.connection().connection.rollback()


def get_instance_checks(session, instance_id):
    # Returns enabled alerting checks as list of tuples:
    # (name, warning threshold, critical threshold)
    checks = session.query(Check).filter(Check.instance_id == instance_id)
    return [(c.name, c.warning, c.critical)
            for c in checks if c.enabled]


def populate_host_checks(session, host_id, instance_id, hostinfo):
    # Populate checks table with bootstraped checks if needed
    for bc in bootstrap_checks(hostinfo):
        # Do not try to add new check if exists
        if session.query(Check).filter(
                Check.host_id == host_id,
                Check.instance_id == instance_id,
                Check.name == bc[0]).count() > 0:
            continue
        c = Check(host_id=host_id,
                  instance_id=instance_id,
                  name=bc[0],
                  enabled=True,
                  warning=bc[1],
                  critical=bc[2],
                  description=check_specs.get(bc[0], {}).get('description'))
        session.add(c)
    session.commit()
