# -*- coding: utf-8 -*-
import logging
import os
from textwrap import dedent

import tornado.web
import tornado.escape

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import ProgrammingError, IntegrityError
from sqlalchemy.sql import text
from psycopg2.extensions import AsIs

from temboardui.toolkit import taskmanager
from temboardui.application import (
    get_roles_by_instance,
    send_mail,
    send_sms,
)
from temboardui.model.orm import (
    Instances,
)

from .model.orm import (
    Check,
    CheckState,
    Host,
    Instance,
)
from .alerting import (
    check_specs,
)
from .handlers import blueprint


logger = logging.getLogger(__name__)
workers = taskmanager.WorkerSet()


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


@workers.register(pool_size=1)
def aggregate_data_worker(app):
    # Worker in charge of aggregate data
    try:
        dbconf = app.config.repository
        dburi = 'postgresql://{user}:{pwd}@:{p}/{db}?host={h}'.format(
                    user=dbconf['user'],
                    pwd=dbconf['password'],
                    h=dbconf['host'],
                    p=dbconf['port'],
                    db=dbconf['dbname'])
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


@workers.register(pool_size=1)
def history_tables_worker(app):
    # Worker in charge of history tables
    try:
        dbconf = app.config.repository
        dburi = 'postgresql://{user}:{pwd}@:{p}/{db}?host={h}'.format(
                    user=dbconf['user'],
                    pwd=dbconf['password'],
                    h=dbconf['host'],
                    p=dbconf['port'],
                    db=dbconf['dbname'])
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


@workers.register(pool_size=10)
def check_data_worker(app, host_id, instance_id, data):
    # Worker in charge of checking preprocessed monitoring values
    specs = check_specs
    dbconf = app.config.repository
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
            # State has changed since last time
            if cs.state != state:
                taskmanager.schedule_task(
                    'notify_state_change',
                    listener_addr=os.path.join(app.config.temboard.home,
                                               '.tm.socket'),
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


@workers.register(pool_size=1)
def purge_data_worker(app):
    """Background worker in charge of purging monitoring data. Purge policy
    is based on purge_after parameter from monitoring section. purger_after
    defines the number of day of data to keep, from now. Default value means
    there is no purge policy.
    """

    logger.setLevel(app.config.logging.level)
    logger.info("Starting monitoring data purge worker.")

    if not app.config.monitoring.purge_after:
        logger.info("No purge policy, end.")
        return

    dburi = 'postgresql://{user}:{pwd}@:{p}/{db}?host={h}'.format(
        user=app.config.repository['user'],
        pwd=app.config.repository['password'],
        h=app.config.repository['host'],
        p=app.config.repository['port'],
        db=app.config.repository['dbname'],
    )
    engine = create_engine(dburi)

    with engine.connect() as conn:
        # Get tablename list to purge from metric_tables_config()
        res = conn.execute(
            dedent("""
                SELECT
                    tablename
                FROM (
                    SELECT
                        tablename_prefix||'_'||suffix AS tablename
                    FROM
                        json_object_keys(monitoring.metric_tables_config()) AS tablename_prefix,
                        UNNEST(ARRAY['30m_current', '6h_current', 'current', 'history']) AS suffix
                ) AS q
                WHERE EXISTS (
                    SELECT 1
                    FROM
                        pg_catalog.pg_tables AS pgt
                    WHERE
                        pgt.tablename=q.tablename
                        AND pgt.schemaname = 'monitoring'
                )
                ORDER BY tablename;
            """)  # noqa
        )
        tablenames = [r['tablename'] for r in res.fetchall()]
        tablenames.extend(['state_changes', 'check_changes'])

        purge_query_base = "DELETE FROM :tablename WHERE "

        for tablename in tablenames:

            # With history tables, we have to deal with tstzrange
            if tablename.endswith("_history"):
                query = purge_query_base + \
                        "NOT (history_range && tstzrange(NOW() " + \
                        "- ':nday days'::INTERVAL, NOW()))"
            else:
                query = purge_query_base + \
                        "datetime < (NOW() - ':nday days'::INTERVAL)"

            logger.debug("Purging table %s", tablename)
            t = conn.begin()
            try:
                res_delete = conn.execute(
                    text(query),
                    tablename=AsIs("monitoring.%s" % tablename),
                    nday=app.config.monitoring.purge_after,
                )
                t.commit()
            except (ProgrammingError, IntegrityError) as e:
                logger.exception(e)
                logger.error("Could not delete data from table %s", tablename)
                t.rollback()
                continue

            if res_delete.rowcount > 0:
                logger.info("Table %s purged, %s rows deleted",
                            tablename, res_delete.rowcount)

    logger.info("End of monitoring data purge worker.")


@workers.register(pool_size=1)
def notify_state_change(app, check_id, key, value, state, prev_state):
    # check if at least one notifications transport is configured
    # if it's not the case pass
    notifications_conf = app.config.notifications
    smtp_host = notifications_conf.smtp_host
    smtp_port = notifications_conf.smtp_port
    smtp_tls = notifications_conf.smtp_tls
    smtp_login = notifications_conf.smtp_login
    smtp_password = notifications_conf.smtp_password
    smtp_from_addr = notifications_conf.smtp_from_addr

    if not smtp_host and \
       not notifications_conf.get('twilio_account_sid', None):
        logger.info("No SMTP nor SMS service configured, "
                    "notification not sent")
        return

    # Worker in charge of sending notifications
    dbconf = app.config.repository
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

    check = worker_session.query(Check).filter(
        Check.check_id == check_id,
    ).join(Instance).join(Host).one()

    port = check.instance.port
    hostname = check.instance.host.hostname
    instance = worker_session.query(Instances).filter(
        Instances.pg_port == port,
        Instances.hostname == hostname,
    ).one()

    # don't notify if notifications are disabled for this instance
    if not instance.notify:
        return

    specs = check_specs
    spec = specs.get(check.name)

    message = ''
    if state != 'OK':
        message = spec.get('message').format(
            key=key,
            check=check.name,
            value=value,
            threshold=getattr(check, state.lower()),
        )

    description = spec.get('description')
    subject = '[temBoard] {state} {hostname} - {description}' \
        .format(hostname=hostname, state=state, description=description)
    link = 'https://%s:%d/server/%s/%d/alerting/%s' % (
        app.config.temboard.address,
        app.config.temboard.port,
        instance.agent_address,
        instance.agent_port,
        check.name)

    direction = '➚' if prev_state == 'OK' or state == 'CRITICAL' else '➘'

    body = '''
    Instance: {hostname}:{port}
    Description: {description}
    Status: {direction} {state} (prev. {prev_state})
    {message}
    {link}
    '''.format(
        hostname=hostname,
        port=instance.agent_port,
        description=description,
        direction=direction,
        state=state,
        prev_state=prev_state,
        message=message,
        link=link,
    )

    roles = get_roles_by_instance(worker_session,
                                  instance.agent_address,
                                  instance.agent_port)

    emails = [role.role_email for role in roles if role.role_email]
    if len(emails):
        send_mail(smtp_host, smtp_port, subject, body, emails, smtp_tls,
                  smtp_login, smtp_password,  smtp_from_addr)

    phones = [role.role_phone for role in roles if role.role_phone]
    if len(phones):
        send_sms(app.config.notifications, body, phones)


@taskmanager.bootstrap()
def monitoring_bootstrap(context):
    yield taskmanager.Task(
            worker_name='aggregate_data_worker',
            id='aggregate_data',
            redo_interval=30 * 60,  # Repeat each 30m,
            options={},
    )
    yield taskmanager.Task(
            worker_name='history_tables_worker',
            id='history_tables',
            redo_interval=3 * 60 * 60,  # Repeat each 3h
            options={},
    )
    yield taskmanager.Task(
            worker_name='purge_data_worker',
            id='purge_data',
            redo_interval=24 * 60 * 60,  # Repeat each 24h
            options={},
    )
