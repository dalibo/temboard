import functools
import logging
from datetime import datetime, timedelta
from textwrap import dedent

from temboardtoolkit.errors import UserError

logger = logging.getLogger(__package__)


def insert_metrics(session, host_id, instance_id, data, labels=None, max_duration=30):
    start = datetime.utcnow()
    max_duration = timedelta(seconds=max_duration)
    labels = labels or {}

    for metric_name in list(data.keys()):
        call_duration = datetime.utcnow() - start
        if call_duration >= max_duration:
            logger.warning(
                "Metrics insertion is too long. Maybe another task is locking tables."
            )
            logger.warning(
                "Aborting metrics insertion. Retrying in less than a minute."
            )
            raise UserError("Metrics insertion takes more than %s." % max_duration)

        # Do not try to insert empty lines
        if data[metric_name] is None:
            continue
        if len(data[metric_name]) == 0:
            continue

        for record in generate_logfmt_records(metric_name, data[metric_name]):
            try:
                logger.debug(
                    "up=1 %s %s",
                    " ".join(["%s=%s" % i for i in labels.items()]),
                    " ".join(["%s=%s" % i for i in record.items()]),
                )
            except Exception:
                logger.exception("Failed to format logfmt.")

        # Insert data
        for metric_data in data[metric_name]:
            logger.debug("Inserting data for metric %s.", metric_name)
            if metric_name == "sessions":
                insert_metric_sessions(session, instance_id, metric_data)
            elif metric_name == "xacts":
                insert_metric_xacts(session, instance_id, metric_data)
            elif metric_name == "locks":
                insert_metric_locks(session, instance_id, metric_data)
            elif metric_name == "blocks":
                insert_metric_blocks(session, instance_id, metric_data)
            elif metric_name == "bgwriter":
                insert_metric_bgwriter(session, instance_id, metric_data)
            elif metric_name == "db_size":
                insert_metric_db_size(session, instance_id, metric_data)
            elif metric_name == "tblspc_size":
                insert_metric_tblspc_size(session, instance_id, metric_data)
            elif metric_name == "filesystems_size":
                insert_metric_fs_size(session, host_id, metric_data)
            elif metric_name == "temp_files_size_delta":
                insert_metric_temp_files_size_delta(session, instance_id, metric_data)
            elif metric_name == "wal_files":
                insert_metric_wal_files(session, instance_id, metric_data)
            elif metric_name == "cpu":
                insert_metric_cpu(session, host_id, metric_data)
            elif metric_name == "process":
                insert_metric_process(session, host_id, metric_data)
            elif metric_name == "memory":
                insert_metric_memory(session, host_id, metric_data)
            elif metric_name == "loadavg":
                insert_metric_loadavg(session, host_id, metric_data)
            elif metric_name == "vacuum_analyze":
                insert_metric_vacuum_analyze(session, instance_id, metric_data)
            elif metric_name == "replication_lag":
                insert_metric_replication_lag(session, instance_id, metric_data)
            elif metric_name == "replication_connection":
                insert_metric_replication_connection(session, instance_id, metric_data)
            elif metric_name == "heap_bloat":
                insert_metric_heap_bloat(session, instance_id, metric_data)
            elif metric_name == "btree_bloat":
                insert_metric_btree_bloat(session, instance_id, metric_data)

            session.commit()


def handle_keyerror(fun):
    metric_name = fun.__name__.replace("insert_metric_", "")

    @functools.wraps(fun)
    def wrapper(*a, **kw):
        try:
            return fun(*a, **kw)
        except KeyError as e:
            logger.warning("Missing point %s for %s.", e.args[0], metric_name)

    return wrapper


def insert_availability(session, dt, instance_id, available):
    session.execute(
        dedent("""
        SELECT monitoring.insert_instance_availability(
            :dt,
            :instance_id,
            :available
        )
        """),
        dict(dt=dt, instance_id=instance_id, available=available),
    )


@handle_keyerror
def insert_metric_sessions(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_sessions_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric["datetime"],
            instance_id=instance_id,
            dbname=metric["dbname"],
            row=(
                None,
                metric["active"],
                metric["waiting"],
                metric["idle"],
                metric["idle_in_xact"],
                metric["idle_in_xact_aborted"],
                metric["fastpath"],
                metric["disabled"],
                metric["no_priv"],
            ),
        ),
    )


@handle_keyerror
def insert_metric_xacts(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_xacts_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric["datetime"],
            instance_id=instance_id,
            dbname=metric["dbname"],
            row=(
                None,
                str(metric["measure_interval"]),
                metric["n_commit"],
                metric["n_rollback"],
            ),
        ),
    )


@handle_keyerror
def insert_metric_locks(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_locks_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric["datetime"],
            instance_id=instance_id,
            dbname=metric["dbname"],
            row=(
                None,
                metric["access_share"],
                metric["row_share"],
                metric["row_exclusive"],
                metric["share_update_exclusive"],
                metric["share"],
                metric["share_row_exclusive"],
                metric["exclusive"],
                metric["access_exclusive"],
                metric["siread"],
                metric["waiting_access_share"],
                metric["waiting_row_share"],
                metric["waiting_row_exclusive"],
                metric["waiting_share_update_exclusive"],
                metric["waiting_share"],
                metric["waiting_share_row_exclusive"],
                metric["waiting_exclusive"],
                metric["waiting_access_exclusive"],
            ),
        ),
    )


@handle_keyerror
def insert_metric_blocks(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_blocks_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric["datetime"],
            instance_id=instance_id,
            dbname=metric["dbname"],
            row=(
                None,
                str(metric["measure_interval"]),
                metric["blks_read"],
                metric["blks_hit"],
                metric["hitmiss_ratio"],
            ),
        ),
    )


@handle_keyerror
def insert_metric_bgwriter(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_bgwriter_current
            VALUES (:dt, :instance_id, :row)
        """),
        dict(
            dt=metric["datetime"],
            instance_id=instance_id,
            row=(
                None,
                str(metric["measure_interval"]),
                metric["checkpoints_timed"],
                metric["checkpoints_req"],
                metric["checkpoint_write_time"],
                metric["checkpoint_sync_time"],
                metric["buffers_checkpoint"],
                metric["buffers_clean"],
                metric["maxwritten_clean"],
                metric["buffers_backend"],
                metric["buffers_backend_fsync"],
                metric["buffers_alloc"],
                metric["stats_reset"],
            ),
        ),
    )


@handle_keyerror
def insert_metric_db_size(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_db_size_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric["datetime"],
            instance_id=instance_id,
            dbname=metric["dbname"],
            row=(None, metric["size"]),
        ),
    )


@handle_keyerror
def insert_metric_tblspc_size(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_tblspc_size_current
            VALUES (:dt, :instance_id, :spcname, :row)
        """),
        dict(
            dt=metric["datetime"],
            instance_id=instance_id,
            spcname=metric["spcname"],
            row=(None, metric["size"]),
        ),
    )


@handle_keyerror
def insert_metric_fs_size(session, host_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_filesystems_size_current
            VALUES (:dt, :host_id, :mount_point, :row)
        """),
        dict(
            dt=metric["datetime"],
            host_id=host_id,
            mount_point=metric["mount_point"],
            row=(None, metric["used"], metric["total"], metric["device"]),
        ),
    )


@handle_keyerror
def insert_metric_temp_files_size_delta(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_temp_files_size_delta_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric["datetime"],
            instance_id=instance_id,
            dbname=metric["dbname"],
            row=(None, str(metric["measure_interval"]), metric["size"]),
        ),
    )


@handle_keyerror
def insert_metric_wal_files(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_wal_files_current
            VALUES (:dt, :instance_id, :row)
        """),
        dict(
            dt=metric["datetime"],
            instance_id=instance_id,
            row=(
                None,
                str(metric["measure_interval"]),
                metric["written_size"],
                metric["current_location"],
                metric["total"],
                metric["archive_ready"],
                metric["total_size"],
            ),
        ),
    )


@handle_keyerror
def insert_metric_cpu(session, host_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_cpu_current
            VALUES (:dt, :host_id, :cpu, :row)
        """),
        dict(
            dt=metric["datetime"],
            host_id=host_id,
            cpu=metric["cpu"],
            row=(
                None,
                str(metric["measure_interval"]),
                metric["time_user"],
                metric["time_system"],
                metric["time_idle"],
                metric["time_iowait"],
                metric["time_steal"],
            ),
        ),
    )


@handle_keyerror
def insert_metric_process(session, host_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_process_current
            VALUES (:dt, :host_id, :row)
        """),
        dict(
            dt=metric["datetime"],
            host_id=host_id,
            row=(
                None,
                str(metric["measure_interval"]),
                metric["context_switches"],
                metric["forks"],
                metric["procs_running"],
                metric["procs_blocked"],
                metric["procs_total"],
            ),
        ),
    )


@handle_keyerror
def insert_metric_memory(session, host_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_memory_current
            VALUES (:dt, :host_id, :row)
        """),
        dict(
            dt=metric["datetime"],
            host_id=host_id,
            row=(
                None,
                metric["mem_total"],
                metric["mem_used"],
                metric["mem_free"],
                metric["mem_buffers"],
                metric["mem_cached"],
                metric["swap_total"],
                metric["swap_used"],
            ),
        ),
    )


@handle_keyerror
def insert_metric_loadavg(session, host_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_loadavg_current
            VALUES (:dt, :host_id, :row)
        """),
        dict(
            dt=metric["datetime"],
            host_id=host_id,
            row=(None, metric["load1"], metric["load5"], metric["load15"]),
        ),
    )


@handle_keyerror
def insert_metric_vacuum_analyze(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_vacuum_analyze_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric["datetime"],
            instance_id=instance_id,
            dbname=metric["dbname"],
            row=(
                None,
                str(metric["measure_interval"]),
                metric["n_vacuum"],
                metric["n_analyze"],
                metric["n_autovacuum"],
                metric["n_autoanalyze"],
            ),
        ),
    )


@handle_keyerror
def insert_metric_replication_lag(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_replication_lag_current
            VALUES (:dt, :instance_id, :row)
        """),
        dict(dt=metric["datetime"], instance_id=instance_id, row=(None, metric["lag"])),
    )


@handle_keyerror
def insert_metric_replication_connection(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_replication_connection_current
            VALUES (:dt, :instance_id, :upstream, :row)
        """),
        dict(
            dt=metric["datetime"],
            instance_id=instance_id,
            upstream=metric["upstream"],
            row=(None, metric["connected"]),
        ),
    )


@handle_keyerror
def insert_metric_heap_bloat(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_heap_bloat_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric["datetime"],
            instance_id=instance_id,
            dbname=metric["dbname"],
            row=(None, metric["ratio"]),
        ),
    )


@handle_keyerror
def insert_metric_btree_bloat(session, instance_id, metric):
    session.execute(
        dedent("""
            INSERT INTO monitoring.metric_btree_bloat_current
            VALUES (:dt, :instance_id, :dbname, :row)
        """),
        dict(
            dt=metric["datetime"],
            instance_id=instance_id,
            dbname=metric["dbname"],
            row=(None, metric["ratio"]),
        ),
    )


def generate_logfmt_records(metric, points):
    # Generate flat key-value record from temBoard metrics data for logfmt.
    if metric not in ("xacts",):
        return
    for point in points:
        record = dict()
        for k, v in point.items():
            if k in ("datetime", "port", "measure_interval"):
                continue
            if k in ("dbname",):
                logkey = k
            else:
                logkey = f"{metric}_{k}"
            record[logkey] = v
        yield record
