# coding: utf-8
from textwrap import dedent


def insert_availability(session, dt, instance_id, available):
    session.execute(
        dedent("""
        SELECT monitoring.insert_instance_availability(
            :dt,
            :instance_id,
            :available
        )
        """),
        dict(dt=dt, instance_id=instance_id, available=available)
    )


def insert_metric_sessions(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_sessions_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric['datetime'],
            instance_id=instance_id,
            dbname=metric['dbname'],
            row=(
                None,
                metric['active'],
                metric['waiting'],
                metric['idle'],
                metric['idle_in_xact'],
                metric['idle_in_xact_aborted'],
                metric['fastpath'],
                metric['disabled'],
                metric['no_priv']
            )
        )
    )


def insert_metric_xacts(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_xacts_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric['datetime'],
            instance_id=instance_id,
            dbname=metric['dbname'],
            row=(
                None,
                str(metric['measure_interval']),
                metric['n_commit'],
                metric['n_rollback']
            )
        )
    )


def insert_metric_locks(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_locks_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric['datetime'],
            instance_id=instance_id,
            dbname=metric['dbname'],
            row=(
                None,
                metric['access_share'],
                metric['row_share'],
                metric['row_exclusive'],
                metric['share_update_exclusive'],
                metric['share'],
                metric['share_row_exclusive'],
                metric['exclusive'],
                metric['access_exclusive'],
                metric['siread'],
                metric['waiting_access_share'],
                metric['waiting_row_share'],
                metric['waiting_row_exclusive'],
                metric['waiting_share_update_exclusive'],
                metric['waiting_share'],
                metric['waiting_share_row_exclusive'],
                metric['waiting_exclusive'],
                metric['waiting_access_exclusive']
            )
        )
    )


def insert_metric_blocks(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_blocks_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric['datetime'],
            instance_id=instance_id,
            dbname=metric['dbname'],
            row=(
                None,
                str(metric['measure_interval']),
                metric['blks_read'],
                metric['blks_hit'],
                metric['hitmiss_ratio']
            )
        )
    )


def insert_metric_bgwriter(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_bgwriter_current
            VALUES (:dt, :instance_id, :row)
        """),
        dict(
            dt=metric['datetime'],
            instance_id=instance_id,
            row=(
                None,
                str(metric['measure_interval']),
                metric['checkpoints_timed'],
                metric['checkpoints_req'],
                metric['checkpoint_write_time'],
                metric['checkpoint_sync_time'],
                metric['buffers_checkpoint'],
                metric['buffers_clean'],
                metric['maxwritten_clean'],
                metric['buffers_backend'],
                metric['buffers_backend_fsync'],
                metric['buffers_alloc'],
                metric['stats_reset']
            )
        )
    )


def insert_metric_db_size(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_db_size_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric['datetime'],
            instance_id=instance_id,
            dbname=metric['dbname'],
            row=(
                None,
                metric['size']
            )
        )
    )


def insert_metric_tblspc_size(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_tblspc_size_current
            VALUES (:dt, :instance_id, :spcname, :row)
        """),
        dict(
            dt=metric['datetime'],
            instance_id=instance_id,
            spcname=metric['spcname'],
            row=(
                None,
                metric['size']
            )
        )
    )


def insert_metric_fs_size(session, host_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_filesystems_size_current
            VALUES (:dt, :host_id, :mount_point, :row)
        """),
        dict(
            dt=metric['datetime'],
            host_id=host_id,
            mount_point=metric['mount_point'],
            row=(
                None,
                metric['used'],
                metric['total'],
                metric['device']
            )
        )
    )


def insert_metric_temp_files_size_delta(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_temp_files_size_delta_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric['datetime'],
            instance_id=instance_id,
            dbname=metric['dbname'],
            row=(
                None,
                str(metric['measure_interval']),
                metric['size']
            )
        )
    )


def insert_metric_wal_files(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_wal_files_current
            VALUES (:dt, :instance_id, :row)
        """),
        dict(
            dt=metric['datetime'],
            instance_id=instance_id,
            row=(
                None,
                str(metric['measure_interval']),
                metric['written_size'],
                metric['current_location'],
                metric['total'],
                metric['archive_ready'],
                metric['total_size']
            )
        )
    )


def insert_metric_cpu(session, host_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_cpu_current
            VALUES (:dt, :host_id, :cpu, :row)
        """),
        dict(
            dt=metric['datetime'],
            host_id=host_id,
            cpu=metric['cpu'],
            row=(
                None,
                str(metric['measure_interval']),
                metric['time_user'],
                metric['time_system'],
                metric['time_idle'],
                metric['time_iowait'],
                metric['time_steal']
            )
        )
    )


def insert_metric_process(session, host_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_process_current
            VALUES (:dt, :host_id, :row)
        """),
        dict(
            dt=metric['datetime'],
            host_id=host_id,
            row=(
                None,
                str(metric['measure_interval']),
                metric['context_switches'],
                metric['forks'],
                metric['procs_running'],
                metric['procs_blocked'],
                metric['procs_total']
            )
        )
    )


def insert_metric_memory(session, host_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_memory_current
            VALUES (:dt, :host_id, :row)
        """),
        dict(
            dt=metric['datetime'],
            host_id=host_id,
            row=(
                None,
                metric['mem_total'],
                metric['mem_used'],
                metric['mem_free'],
                metric['mem_buffers'],
                metric['mem_cached'],
                metric['swap_total'],
                metric['swap_used']
            )
        )
    )


def insert_metric_loadavg(session, host_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_loadavg_current
            VALUES (:dt, :host_id, :row)
        """),
        dict(
            dt=metric['datetime'],
            host_id=host_id,
            row=(
                None,
                metric['load1'],
                metric['load5'],
                metric['load15']
            )
        )
    )


def insert_metric_vacuum_analyze(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_vacuum_analyze_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric['datetime'],
            instance_id=instance_id,
            dbname=metric['dbname'],
            row=(
                None,
                str(metric['measure_interval']),
                metric['n_vacuum'],
                metric['n_analyze'],
                metric['n_autovacuum'],
                metric['n_autoanalyze']
            )
        )
    )


def insert_metric_replication_lag(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_replication_lag_current
            VALUES (:dt, :instance_id, :row)
        """),
        dict(
            dt=metric['datetime'],
            instance_id=instance_id,
            row=(
                None,
                metric['lag']
            )
        )
    )


def insert_metric_replication_connection(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_replication_connection_current
            VALUES (:dt, :instance_id, :upstream, :row)
        """),
        dict(
            dt=metric['datetime'],
            instance_id=instance_id,
            upstream=metric['upstream'],
            row=(
                None,
                metric['connected']
            )
        )
    )


def insert_metric_heap_bloat(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_heap_bloat_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric['datetime'],
            instance_id=instance_id,
            dbname=metric['dbname'],
            row=(
                None,
                metric['ratio']
            )
        )
    )


def insert_metric_btree_bloat(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_btree_bloat_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric['datetime'],
            instance_id=instance_id,
            dbname=metric['dbname'],
            row=(
                None,
                metric['ratio']
            )
        )
    )


def get_host_id(session, hostname):
    row = session.execute(
        "SELECT host_id FROM monitoring.hosts WHERE hostname = :hostname",
        dict(hostname=hostname)
    ).fetchone()
    return row[0] if row else None


def get_instance_id(session, host_id, port):
    row = session.execute(
        dedent("""
            SELECT instance_id
            FROM monitoring.instances
            WHERE host_id = :host_id AND port = :port
        """),
        dict(host_id=host_id, port=port)
    ).fetchone()
    return row[0] if row else None


def get_agent_key(session, hostname, pg_data, pg_port):
    row = session.execute(
        dedent("""
            SELECT agent_key
            FROM application.instances
            WHERE hostname = :hostname AND pg_data=:pg_data
            AND pg_port = :pg_port
            LIMIT 1
        """),
        dict(
            hostname=hostname,
            pg_data=pg_data,
            pg_port=pg_port
        )
    ).fetchone()
    return row[0] if row else None


def get_agent_keys(session, hostname):
    return session.execute(
        dedent("""
            SELECT agent_key
            FROM application.instances
            WHERE hostname = :hostname
        """),
        dict(
            hostname=hostname
        )
    ).fetchall()


def append_state_changes(
    session, dt, check_id, state, key, value, warning, critical
):
    session.execute(
        dedent("""
            SELECT monitoring.append_state_changes(
                :datetime, :check_id, :state, :key, :value, :warning, :critical
            )
        """),
        dict(
            datetime=dt,
            check_id=check_id,
            state=state,
            key=key,
            value=value,
            warning=warning,
            critical=critical
        )
    )


def purge_check_states(session, check_id, keys):
    session.execute(
        dedent("""
            DELETE FROM monitoring.check_states
            WHERE check_id = :check_id AND NOT (key = ANY(:keys))
        """),
        dict(
            check_id=check_id,
            keys=keys
        )
    )


def undef_check_states(session, all_ids, to_keep_ids):
    session.execute(
        dedent("""
            UPDATE monitoring.check_states
            SET state = 'UNDEF'
            WHERE
                check_id = ANY(:all_ids)
                AND NOT (check_id = ANY(:to_keep_ids))
        """),
        dict(
            all_ids=all_ids,
            to_keep_ids=to_keep_ids,
        )
    )
