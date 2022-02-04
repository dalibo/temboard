# -*- coding: utf-8 -*-
#
# Somes notes on monitoring in temBoard
#
# Metrics are stored in different tables:
#
# - metric_*_current stores metrics one row per metric point
# - metric_*_30m_current is a compacted COPY of _current by interval
# - metric_*_history aggregates points per time interavl
#
# Tasks:
#
# - schedule_collector(): schedule a collector task for each agent in
#   inventory.
# - collector(host, port, key) inserts metrics history in metric_*_current
#   table.
# - history_tables_worker() move data from metric_*_current to
#   metric_*_history, grouped by time range. metric table is truncated
# - aggregate_data_worker() aggregates data in metric_*_30m_current and
#   metric_*_6h_current.
#

from builtins import str
from datetime import datetime, timedelta
import json
import hashlib
import logging
import os
from textwrap import dedent
try:
    # python2
    from urllib2 import URLError, HTTPError
    from urllib import quote
except Exception:
    # python3
    from urllib.error import URLError, HTTPError
    from urllib.parse import quote

import tornado.web
import tornado.escape

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import ProgrammingError, IntegrityError, DataError
from sqlalchemy.sql import text

from psycopg2.extensions import AsIs

from temboardui.toolkit import taskmanager
from temboardui.application import (
    get_roles_by_instance,
    send_mail,
    send_sms,
)
from temboardui.temboardclient import temboard_request
from temboardui.model.orm import Instances
from temboardui.model import worker_engine

from .model.orm import (
    Check,
    CollectorStatus,
    Host,
    Instance,
)
from .model.db import insert_availability
from .alerting import (
    check_specs,
)
from .handlers import blueprint
from .tools import (
    check_preprocessed_data,
    get_host_id,
    get_instance_checks,
    get_instance_id,
    insert_metrics,
    merge_agent_info,
    populate_host_checks,
    preprocess_data,
    update_collector_status,
    Stopwatch,
)

logger = logging.getLogger(__name__)
PLUGIN_NAME = 'monitoring'
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
    stopwatch = Stopwatch()
    engine = worker_engine(app.config.repository)
    with engine.connect() as conn:
        conn.execute("SET search_path TO monitoring")
        res = conn.execute("SELECT * FROM metric_tables_config()")
        tables_config, = res.fetchone()
        for config in tables_config.values():
            logger.info("Aggregating data for metric %s.", config['name'])
            try:
                with conn.begin(), stopwatch:
                    res = conn.execute(
                        "SELECT * FROM aggregate_data_single(%s, %s, %s)", (
                            config['name'], config['record_type'],
                            config['aggregate'],
                        )
                    )
                    table_name, nb_rows = res.fetchone()
                logger.debug(
                    "table=%s insert=%s timedelta=%s",
                    table_name, nb_rows, stopwatch.last_delta)
            except Exception as e:
                logger.error("Failed to archive data: %s.", e)
                # search_path is lost on exception. Define it again.
                conn.execute("SET search_path TO monitoring")

    logger.info("Monitoring data aggregation done.")
    logger.debug("Total time in SQL %s.", stopwatch.delta)


@workers.register(pool_size=1)
def history_tables_worker(app):
    # Archive monitoring metric tables.
    #
    # Copy contents of every metric_*_current tables into corresponding
    # metric_*_history, aggregated. Then truncate _current tables.
    #
    # This task is triggered every 3 hours by monitoring_boostrap() below.
    #
    stopwatch = Stopwatch()
    engine = worker_engine(app.config.repository)
    with engine.connect() as conn:
        conn.execute("SET search_path TO monitoring")
        res = conn.execute("SELECT * FROM metric_tables_config()")
        tables_config, = res.fetchone()
        for config in tables_config.values():
            logger.info("Archiving data for metric %s.", config['name'])
            try:
                with conn.begin(), stopwatch:
                    res = conn.execute(
                        "SELECT * FROM archive_current_metrics(%s, %s, %s)", (
                            config['name'], config['record_type'],
                            config['history'],
                        )
                    )

                    table_name, nb_rows = res.fetchone()
                logger.debug(
                    "table=%s insert=%s timedelta=%s",
                    table_name, nb_rows, stopwatch.last_delta)
            except Exception as e:
                logger.error("Failed to archive data: %s.", e)
                # search_path is lost on exception. Define it again.
                conn.execute("SET search_path TO monitoring")

    logger.info("Monitoring data archiving done.")
    logger.debug("Total time in SQL %s.", stopwatch.delta)


@workers.register(pool_size=10)
def check_data_worker(app, host_id, instance_id, data):
    # Worker in charge of checking preprocessed monitoring values
    engine = worker_engine(app.config.repository)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    worker_session = Session()

    check_preprocessed_data(
        worker_session,
        host_id,
        instance_id,
        data,
        app.config.temboard.home
    )

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

    engine = worker_engine(app.config.repository)

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
    engine = worker_engine(app.config.repository)
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


@workers.register(pool_size=1)
def schedule_collector(app):
    """Worker function in charge of scheduling collector (pull mode)."""

    logger.setLevel(app.config.logging.level)
    logger.info("Starting collector scheduler.")

    engine = worker_engine(app.config.repository)
    with engine.connect() as conn:
        # Get the list of agents
        res = conn.execute(
            "SELECT agent_address, agent_port, agent_key "
            "FROM application.instances ORDER BY 1, 2"
        )

        for agent_address, agent_port, agent_key in res.fetchall():
            # For each registered agent, let's start a new data collector

            # Build a unique Task id based on agent address and port
            agent_id = "%s:%s" % (agent_address, agent_port)
            task_id = hashlib.md5(agent_id.encode("utf-8")).hexdigest()[:8]

            logger.info("Scheduling collector for agent %s.", agent_id)

            taskmanager.schedule_task(
                'collector',
                listener_addr=os.path.join(
                    app.config.temboard.home, '.tm.socket'
                ),
                id=task_id,
                options=dict(
                    address=agent_address,
                    port=agent_port,
                    key=agent_key,
                ),
                expire=0,
            )

    logger.info("End of collector scheduler.")


@workers.register(pool_size=20)
def collector(app, address, port, key):
    agent_id = "%s:%s" % (address, port)
    logger.info("Starting collector for %s.", agent_id)

    discover_data = dict()

    # First, we need to call discover API because we want to know the hostname
    logger.info("Discovering hostname from agent %s.", agent_id)
    url = 'https://%s:%s/discover' % (address, port)
    logger.debug("Calling %s.", url)

    try:
        response = temboard_request(
            app.config.temboard.ssl_ca_cert_file,
            'GET',
            url,
            headers={"Content-type": "application/json"},
        )
    except (URLError, HTTPError):
        logger.error("Could not get response from %s.", url)
        logger.error("Agent or host are down.")
        return

    discover_data = json.loads(response)
    logger.debug(discover_data)

    # Start new ORM DB session
    engine = worker_engine(app.config.repository)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    worker_session = Session()

    host_id = instance_id = None
    # Agent monitoring API endpoint
    history_url = 'https://%s:%s/monitoring/history?key=%s&limit=100' % (
        address, port, quote(key)
    )

    try:
        # Trying to find host_id, instance_id and the datetime of the latest
        # inserted record.

        # Find host_id and instance_id by hostname and PG port
        host_id = get_host_id(worker_session, discover_data['hostname'])
        instance_id = get_instance_id(
            worker_session,
            host_id,
            discover_data['pg_port']
        )
        logger.info(
            "Found host #%s and instance #%s for agent %s, hostname %s.",
            host_id, instance_id, agent_id, discover_data['hostname'])
    except Exception:
        # This case happens on the very first pull when no data have been
        # previously added.
        logger.warning(
            "Could not find host or instance records in monitoring inventory "
            "tables for agent %s.", agent_id,
        )
    else:
        # Get last inserted data timestamp from collector status
        collector_status = worker_session.query(CollectorStatus).filter(
            CollectorStatus.instance_id == instance_id
        ).first()

        if collector_status and collector_status.last_insert:
            start = (
                collector_status.last_insert + timedelta(seconds=1)
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            history_url += "&start=%s" % start

    # Finally, let's call /monitoring/history agent API for getting metrics
    # history.
    try:
        logger.info("Querying monitoring history from agent %s.", agent_id)
        logger.debug("Calling %s.", history_url)
        response = temboard_request(
            app.config.temboard.ssl_ca_cert_file,
            'GET',
            history_url,
            headers={"Content-type": "application/json"},
        )
        response = json.loads(response)
    except HTTPError as e:
        if e.code == 404:
            logger.error("Agent version does not support pull mode. "
                         "Please consider upgrading to version 5 at least.")
        else:
            logger.exception(str(e))
            # Update collector status only if instance_id is known
            if instance_id:
                update_collector_status(
                    worker_session,
                    instance_id,
                    u'FAIL',
                    last_pull=datetime.utcnow(),
                )
                worker_session.commit()
        worker_session.close()
        return

    if not response:
        logger.info("Agent %s returned no monitoring data.", agent_id)

    for row in response:
        logger.info("Got points for %s at %s.", agent_id, row['datetime'])
        hostinfo = row['hostinfo']
        data = row['data']
        instance = row['instances'][0]
        port = instance['port']
        if 'max_connections' in instance:
            row['data']['max_connections'] = instance['max_connections']

        try:
            # Try to insert collected data

            logger.info("Update the inventory for %s.", agent_id)
            host = merge_agent_info(worker_session, hostinfo, instance)
            instance_id = get_instance_id(worker_session, host.host_id, port)
            logger.info("Insert instance availability for %s.", agent_id)
            insert_availability(
                worker_session,
                row['datetime'],
                instance_id,
                row['instances'][0]['available']
            )
            logger.info("Insert collected metrics for %s.", agent_id)
            insert_metrics(
                worker_session, host.host_id, instance_id, data, dict(
                    agent=agent_id,
                    timestamp=(
                        # transform to ISOFORMAT (same as journalctl)
                        row['datetime'].replace(' +', '+').replace(' ', 'T')
                    ),
                ),
            )
            worker_session.commit()

        except DataError as e:
            # Wrong data type or corrupted data could lead to DataError. In
            # this case we should consider this row as unvalid and move to the
            # next one.
            try:
                last_insert = datetime.strptime(
                    row['datetime'], "%Y-%m-%d %H:%M:%S +0000"
                )
            except ValueError:
                # If row datetime could not be parsed, we should fallback to
                # current datetime. This will result to ignore potential valid
                # rows between row datetime and now, but this is better than
                # letting the collector stucked for ever on an invalid row.
                last_insert = datetime.utcnow()

            logger.exception(str(e))
            worker_session.rollback()
            if instance_id:
                logger.info("Set collector status to FAIL for %s.", host)
                update_collector_status(
                    worker_session,
                    instance_id,
                    u'FAIL',
                    last_pull=datetime.utcnow(),
                    last_insert=last_insert,
                )
                worker_session.commit()
            logger.info("Continue with the next row.")
            continue

        logger.debug("Update collector status for agent %s.", agent_id)
        update_collector_status(
            worker_session,
            instance_id,
            u'OK',
            last_pull=datetime.utcnow(),
            # This is the datetime format used by the agent
            last_insert=datetime.strptime(
                row['datetime'], "%Y-%m-%d %H:%M:%S +0000"
            ),
        )
        worker_session.commit()
        logger.info("Populate checks for %s.", host)
        # ALERTING PART
        populate_host_checks(
            worker_session,
            host.host_id,
            instance_id,
            dict(n_cpu=hostinfo['cpu_count']),
        )
        worker_session.commit()

        logger.info(
            "Apply alerting checks against preprocessed data for agent %s.",
            agent_id)
        try:
            check_preprocessed_data(
                worker_session,
                host.host_id,
                instance_id,
                preprocess_data(
                    row['data'],
                    get_instance_checks(worker_session, instance_id),
                    row['datetime']
                ),
                app.config.temboard.home,
            )
        except Exception:
            logger.exception("Failed to check monitoring data for alerting.")

        logger.debug("Row with datetime=%s inserted", row['datetime'])
        worker_session.commit()

    worker_session.close()
    logger.info("End of collector for agent %s.", agent_id)


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
    yield taskmanager.Task(
            worker_name='schedule_collector',
            id='schedule_collector',
            redo_interval=60,  # Repeat each 60s
            options={},
    )
