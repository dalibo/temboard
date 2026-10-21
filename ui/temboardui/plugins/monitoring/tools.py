import logging
from datetime import datetime, timedelta

from temboardtoolkit.errors import UserError

from .model import db
from .model.orm import CollectorStatus, Host, Instance

logger = logging.getLogger(__package__)


def merge_agent_info(session, host_info, instance_info):
    """Update the host, instance and database information with the
    data received from the agent."""

    try:
        # Try to get host_id, based on hostname
        host_info["host_id"] = db.get_host_id(session, host_info["hostname"])
    except NameError:
        # host not found
        pass

    host = Host.from_dict(host_info)

    # Insert or update host information
    session.merge(host)
    session.flush()
    session.commit()

    # Get host_id in any case
    host_id = db.get_host_id(session, host_info["hostname"])
    # Weird that SA does not update this.
    host.host_id = host_id

    # Only process instances marked as available, since only those
    # have complete information
    if instance_info["available"]:
        try:
            # Try to get instance_id
            instance_info["instance_id"] = db.get_instance_id(
                session, host_id, instance_info["port"]
            )
        except Exception:
            # instance not found
            pass
        instance_info["host_id"] = host_id

        inst = Instance.from_dict(instance_info)
        # Insert or update instance information
        session.merge(inst)
        session.flush()
        session.commit()
    return host


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
                db.insert_metric_sessions(session, instance_id, metric_data)
            elif metric_name == "xacts":
                db.insert_metric_xacts(session, instance_id, metric_data)
            elif metric_name == "locks":
                db.insert_metric_locks(session, instance_id, metric_data)
            elif metric_name == "blocks":
                db.insert_metric_blocks(session, instance_id, metric_data)
            elif metric_name == "bgwriter":
                db.insert_metric_bgwriter(session, instance_id, metric_data)
            elif metric_name == "db_size":
                db.insert_metric_db_size(session, instance_id, metric_data)
            elif metric_name == "tblspc_size":
                db.insert_metric_tblspc_size(session, instance_id, metric_data)
            elif metric_name == "filesystems_size":
                db.insert_metric_fs_size(session, host_id, metric_data)
            elif metric_name == "temp_files_size_delta":
                db.insert_metric_temp_files_size_delta(
                    session, instance_id, metric_data
                )
            elif metric_name == "wal_files":
                db.insert_metric_wal_files(session, instance_id, metric_data)
            elif metric_name == "cpu":
                db.insert_metric_cpu(session, host_id, metric_data)
            elif metric_name == "process":
                db.insert_metric_process(session, host_id, metric_data)
            elif metric_name == "memory":
                db.insert_metric_memory(session, host_id, metric_data)
            elif metric_name == "loadavg":
                db.insert_metric_loadavg(session, host_id, metric_data)
            elif metric_name == "vacuum_analyze":
                db.insert_metric_vacuum_analyze(session, instance_id, metric_data)
            elif metric_name == "replication_lag":
                db.insert_metric_replication_lag(session, instance_id, metric_data)
            elif metric_name == "replication_connection":
                db.insert_metric_replication_connection(
                    session, instance_id, metric_data
                )
            elif metric_name == "heap_bloat":
                db.insert_metric_heap_bloat(session, instance_id, metric_data)
            elif metric_name == "btree_bloat":
                db.insert_metric_btree_bloat(session, instance_id, metric_data)

            session.commit()


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


def update_collector_status(
    session, instance_id, status, last_pull=None, last_push=None, last_insert=None
):
    cs = CollectorStatus()
    cs.instance_id = instance_id
    cs.status = status
    if last_pull:
        cs.last_pull = last_pull
    if last_push:
        cs.last_push = last_push
    if last_insert:
        cs.last_insert = last_insert

    session.merge(cs)
