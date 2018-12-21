import logging
import os

import tornado.web
import tornado.escape

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound

from temboardui.toolkit import taskmanager

from .model.orm import (
    Check,
    CheckState,
)
from .alerting import (
    check_specs,
)
from .handlers import blueprint


logger = logging.getLogger(__name__)


def configuration(config):
    return {}


def get_routes(config):
    plugin_path = os.path.dirname(os.path.realpath(__file__))
    __import__(__name__ + '.handlers.alerting')
    __import__(__name__ + '.handlers.monitoring')
    routes = blueprint.rules + [
        (r"/js/monitoring/(.*)",
         tornado.web.StaticFileHandler, {'path': plugin_path + "/static/js"}),
    ]
    return routes


@taskmanager.worker(pool_size=1)
def aggregate_data_worker(config):
    # Worker in charge of aggregate data
    try:
        conf = config['repository']
        dburi = 'postgresql://{user}:{pwd}@:{p}/{db}?host={h}'.format(
                    user=conf['user'],
                    pwd=conf['password'],
                    h=conf['host'],
                    p=conf['port'],
                    db=conf['dbname'])
        engine = create_engine(dburi)
        with engine.begin() as conn:
            conn.execute("SET search_path TO monitoring")
            logger.debug("Running SQL function monitoring.aggregate_data()")
            res = conn.execute("SELECT * FROM aggregate_data()")
            for row in res.fetchall():
                logger.debug("table=%s insert=%s"
                             % (row['tblname'], row['nb_rows']))
            return
    except Exception as e:
        logger.error('Could not aggregate montitoring data')
        logger.exception(e)
        raise(e)


@taskmanager.worker(pool_size=1)
def history_tables_worker(config):
    # Worker in charge of history tables
    try:
        conf = config['repository']
        dburi = 'postgresql://{user}:{pwd}@:{p}/{db}?host={h}'.format(
                    user=conf['user'],
                    pwd=conf['password'],
                    h=conf['host'],
                    p=conf['port'],
                    db=conf['dbname'])
        engine = create_engine(dburi)
        with engine.connect() as conn:
            conn.execute("SET search_path TO monitoring")
            logger.debug("Running SQL function monitoring.history_tables()")
            res = conn.execute("SELECT * FROM history_tables()")
            for row in res.fetchall():
                logger.debug("table=%s insert=%s"
                             % (row['tblname'], row['nb_rows']))
            conn.execute("COMMIT")
            return
    except Exception as e:
        logger.error('Could not history montitoring tables')
        logger.exception(e)
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        raise(e)


@taskmanager.worker(pool_size=1)
def check_data_worker(dbconf, host_id, instance_id, data):
    # Worker in charge of checking preprocessed monitoring values
    specs = check_specs
    dburi = 'postgresql://{user}:{pwd}@:{p}/{db}?host={h}'.format(
                user=dbconf['user'],
                pwd=dbconf['password'],
                h=dbconf['host'],
                p=dbconf['port'],
                db=dbconf['dbname']
            )
    engine = create_engine(dburi)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    worker_session = Session()
    keys = dict()

    for raw in data:
        datetime = raw.get('datetime')
        name = raw.get('name')
        key = raw.get('key')
        value = raw.get('value')
        warning = raw.get('warning')
        critical = raw.get('critical')

        # Proceed with thresholds comparison
        spec = specs.get(name)
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
            c = worker_session.query(Check).filter(
                    Check.name == unicode(name),
                    Check.host_id == host_id,
                    Check.instance_id == instance_id,
                    Check.enabled == bool(True),
                ).one()
        except NoResultFound:
            continue

        # Update/insert check current state
        try:
            cs = worker_session.query(CheckState).filter(
                    CheckState.check_id == c.check_id,
                    CheckState.key == unicode(key)
                ).one()
            cs.state = unicode(state)
            worker_session.merge(cs)
        except NoResultFound:
            cs = CheckState(check_id=c.check_id, key=unicode(key),
                            state=unicode(state))
            worker_session.add(cs)

        worker_session.flush()
        # Append state change if any to history
        worker_session.execute("SELECT monitoring.append_state_changes(:d, :i,"
                               ":s, :k, :v, :w, :c)",
                               {'d': datetime, 'i': c.check_id, 's': cs.state,
                                'k': cs.key, 'v': value, 'w': warning,
                                'c': critical})

        if c.check_id not in keys:
            keys[c.check_id] = list()
        keys[c.check_id].append(cs.key)

        worker_session.commit()
        worker_session.expunge_all()

    # Purge CheckState
    for check_id, ks in keys.items():
        worker_session.execute("DELETE FROM monitoring.check_states WHERE "
                               "check_id = :check_id AND NOT (key = ANY(:ks))",
                               {'check_id': check_id, 'ks': ks})
        worker_session.commit()

    # check_ids for the given instance
    req = worker_session.query(Check).filter(Check.instance_id == instance_id)
    check_ids = [check.check_id for check in req]

    # Set to UNDEF every unchecked check for the given instance
    # This may happen when postgres is unavailable for example
    worker_session.execute("UPDATE monitoring.check_states "
                           "SET state = 'UNDEF' "
                           "WHERE check_id = ANY(:all_check_ids) AND "
                           "NOT check_id = ANY(:check_ids_to_keep)",
                           {
                               'all_check_ids': check_ids,
                               'check_ids_to_keep': keys.keys()
                           })
    worker_session.commit()

    worker_session.close()


@taskmanager.bootstrap()
def monitoring_bootstrap(context):
    config = context.get('config')
    yield taskmanager.Task(
            worker_name='aggregate_data_worker',
            id='aggregate_data',
            options={'config': config},
            redo_interval=30 * 60  # Repeat each 30m,
    )
    yield taskmanager.Task(
            worker_name='history_tables_worker',
            id='history_tables',
            options={'config': config},
            redo_interval=3 * 60 * 60  # Repeat each 3h
    )
