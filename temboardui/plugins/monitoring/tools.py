from dateutil import parser as parse_datetime
import logging
import os

from sqlalchemy.orm.exc import NoResultFound

from temboardui.web import HTTPError
from temboardui.toolkit import taskmanager

from .model.orm import (
    Check,
    CheckState,
    CollectorStatus,
    Host,
    Instance,
)
from .model import db
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
    """Get host_id by the hostname.
    """
    host_id = db.get_host_id(session, hostname)
    if not host_id:
        raise Exception(
            "Could not find registered host with hostname=%s" % hostname
        )
    return host_id


def get_instance_id(session, host_id, port):
    """Get instance_id by host_id and port.
    """
    instance_id = db.get_instance_id(session, host_id, port)
    if not instance_id:
        raise Exception(
            "Could not find registered instance with host_id=%s and port=%s"
            % (host_id, port)
        )
    return instance_id


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
    """Check that the given key matches with the registered one.
    """
    row_key = db.get_agent_key(session, hostname, pg_data, pg_port)

    if not row_key:
        raise Exception("Could not find agent key.")

    if row_key != agent_key:
        raise Exception("Agent key does not match.")


def check_host_key(session, hostname, agent_key):
    """Check that the given key matches with one of .
    """
    matched = False

    if agent_key in db.get_agent_keys(session, hostname):
        matched = True

    if not matched:
        raise Exception("Agent key does not match.")


def insert_metrics(session, host_id, instance_id, data):

    for metric_name in data.keys():
        # Do not try to insert empty lines
        if data[metric_name] is None:
            continue
        if len(data[metric_name]) == 0:
            continue

        # Insert data
        for metric_data in data[metric_name]:
            if metric_name == 'sessions':
                db.insert_metric_sessions(session, instance_id, metric_data)
            elif metric_name == 'xacts':
                db.insert_metric_xacts(session, instance_id, metric_data)
            elif metric_name == 'locks':
                db.insert_metric_locks(session, instance_id, metric_data)
            elif metric_name == 'blocks':
                db.insert_metric_blocks(session, instance_id, metric_data)
            elif metric_name == 'bgwriter':
                db.insert_metric_bgwriter(session, instance_id, metric_data)
            elif metric_name == 'db_size':
                db.insert_metric_db_size(session, instance_id, metric_data)
            elif metric_name == 'tblspc_size':
                db.insert_metric_tblspc_size(session, instance_id, metric_data)
            elif metric_name == 'filesystems_size':
                db.insert_metric_fs_size(session, host_id, metric_data)
            elif metric_name == 'temp_files_size_delta':
                db.insert_metric_temp_files_size_delta(
                    session, instance_id, metric_data
                )
            elif metric_name == 'wal_files':
                db.insert_metric_wal_files(session, instance_id, metric_data)
            elif metric_name == 'cpu':
                db.insert_metric_cpu(session, host_id, metric_data)
            elif metric_name == 'process':
                db.insert_metric_process(session, host_id, metric_data)
            elif metric_name == 'memory':
                db.insert_metric_memory(session, host_id, metric_data)
            elif metric_name == 'loadavg':
                db.insert_metric_loadavg(session, host_id, metric_data)
            elif metric_name == 'vacuum_analyze':
                db.insert_metric_vacuum_analyze(
                    session, instance_id, metric_data
                )
            elif metric_name == 'replication_lag':
                db.insert_metric_replication_lag(
                    session, instance_id, metric_data
                )
            elif metric_name == 'replication_connection':
                db.insert_metric_replication_connection(
                    session, instance_id, metric_data
                )
            elif metric_name == 'heap_bloat':
                db.insert_metric_heap_bloat(session, instance_id, metric_data)
            elif metric_name == 'btree_bloat':
                db.insert_metric_btree_bloat(session, instance_id, metric_data)


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


def update_collector_status(session, instance_id, status, last_pull=None,
                            last_push=None, last_insert=None):
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


def build_check_task_options(data, host_id, instance_id, checks, timestamp):
    """Build Task options for check_data_worker worker."""

    return dict(
        host_id=host_id,
        instance_id=instance_id,
        data=preprocess_data(data, checks, timestamp),
    )


def preprocess_data(data, checks, timestamp):
    """Preprocess metrics for alerting."""
    ret = list()

    for check in checks:
        spec = check_specs.get(check[0])
        if not spec:
            continue

        try:
            res = spec.get('preprocess')(data)
        except Exception as e:
            logger.warning(
                "Failed to preprocess alerting check '%s': %s", check[0], e,
            )
            continue

        if not isinstance(res, dict):
            res = {'': res}

        for key, value in res.items():
            ret.append(
                dict(
                    datetime=timestamp,
                    name=check[0],
                    key=key,
                    value=value,
                    warning=check[1],
                    critical=check[2]
                )
            )
    return ret


def check_preprocessed_data(session, host_id, instance_id, ppdata, home):
    # Function in charge of checking preprocessed monitoring values
    keys = dict()

    for raw in ppdata:
        dt = raw.get('datetime')
        name = raw.get('name')
        key = raw.get('key')
        value = raw.get('value')
        warning = raw.get('warning')
        critical = raw.get('critical')

        # Proceed with thresholds comparison
        spec = check_specs.get(name)
        state = 'UNDEF'
        if not spec:
            continue
        if not (spec.get('operator')(value, warning)
                or spec.get('operator')(value, critical)):
            state = 'OK'
        if spec.get('operator')(value, warning):
            state = 'WARNING'
        if spec.get('operator')(value, critical):
            state = 'CRITICAL'

        # Try to find enabled check for this host_id with the same name
        try:
            c = session.query(Check).filter(
                Check.name == unicode(name),
                Check.host_id == host_id,
                Check.instance_id == instance_id,
                Check.enabled == bool(True),
            ).one()
        except NoResultFound:
            continue

        # Update/insert check current state
        try:
            cs = session.query(CheckState).filter(
                CheckState.check_id == c.check_id,
                CheckState.key == unicode(key)
            ).one()
            # State has changed since last time
            if cs.state != state:
                taskmanager.schedule_task(
                    'notify_state_change',
                    listener_addr=os.path.join(home, '.tm.socket'),
                    options={
                        'check_id': c.check_id,
                        'key': key,
                        'value': value,
                        'state': state,
                        'prev_state': cs.state
                    },
                    expire=0,
                )
            cs.state = unicode(state)
            session.merge(cs)

        except NoResultFound:
            cs = CheckState(
                check_id=c.check_id, key=unicode(key), state=unicode(state)
            )
            session.add(cs)

        session.flush()
        # Append state change if any to history
        db.append_state_changes(
            session,
            dt,
            c.check_id,
            cs.state,
            cs.key,
            value,
            warning,
            critical,
        )

        if c.check_id not in keys:
            keys[c.check_id] = list()
        keys[c.check_id].append(cs.key)

        session.commit()
        session.expunge_all()

    # Purge CheckState
    for check_id, ks in keys.items():
        db.purge_check_states(session, check_id, ks)
        session.commit()

    # Get the list of check_id for the given instance
    req = session.query(Check).filter(Check.instance_id == instance_id)
    all_check_ids = [check.check_id for check in req]

    # Set to UNDEF each unchecked check for the given instance
    # This may happen when postgres is not available
    db.undef_check_states(session, all_check_ids, keys.keys())
    session.commit()
