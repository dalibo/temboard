import logging
from os import path
import tornado.web
import urllib2
from tornado.escape import json_decode
from tornado.web import (
    HTTPError,
)

from sqlalchemy.orm import (
    sessionmaker,
    scoped_session,
)
from sqlalchemy import create_engine
from temboardui.model.orm import (
    Instances,
)
from temboardui.errors import TemboardUIError

from temboardui.web import (
    Blueprint,
    TemplateRenderer,
    jsonify,
)
from temboardui.plugins.monitoring.tools import (
    get_request_ids,
    parse_start_end,
)
from temboardui.toolkit import taskmanager
from temboardui.temboardclient import (
    temboard_request,
)


logger = logging.getLogger(__name__)
workers = taskmanager.WorkerSet()


blueprint = Blueprint()
plugin_path = path.dirname(path.realpath(__file__))
render_template = TemplateRenderer(plugin_path + '/templates')


def configuration(config):
    return {}


def get_routes(config):
    routes = blueprint.rules + [
        (r"/js/statements/(.*)", tornado.web.StaticFileHandler, {
            'path': plugin_path + "/static/js"
        }),
    ]
    return routes


def get_agent_username(request):
    try:
        agent_username = request.instance.get_profile()['username']
    except Exception:
        agent_username = None
    return agent_username


@blueprint.instance_route(r'/statements/data')
def json_data(request):
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)

    query = """
        SELECT
          statements.datname,
          sum((record).blk_read_time) AS blk_read_time,
          sum((record).blk_write_time) AS blk_write_time,
          sum((record).calls) AS calls,
          sum((record).local_blks_dirtied) AS local_blks_dirtied,
          sum((record).local_blks_hit) AS local_blks_hit,
          sum((record).local_blks_read) AS local_blks_read,
          sum((record).local_blks_written) AS local_blks_written,
          max((record).max_time) AS max_time,
          sum((record).total_time) / sum((record).calls) AS mean_time,
          min((record).min_time) AS min_time,
          sum((record).shared_blks_dirtied) AS shared_blks_dirtied,
          sum((record).shared_blks_hit) AS shared_blks_hit,
          sum((record).shared_blks_read) AS shared_blks_read,
          sum((record).shared_blks_written) AS shared_blks_written,
          sum((record).stddev_time) AS stddev_time,
          sum((record).temp_blks_read) AS temp_blks_read,
          sum((record).temp_blks_written) AS temp_blks_written,
          sum((record).total_time) AS total_time
        FROM statements.statements_history_current AS history
        JOIN statements.statements AS statements ON (
          history.agent_address = statements.agent_address AND
          history.agent_port = statements.agent_port AND
          history.queryid = statements.queryid AND
          history.dbid = statements.dbid AND
          history.userid = statements.userid
        )
        WHERE statements.agent_address = :agent_address
        AND statements.agent_port = :agent_port
        AND history.datetime <@ tstzrange(:start, :end, '[]')
        GROUP BY statements.datname
    """
    statements = request.db_session.execute(
        query,
        dict(agent_address=request.instance.agent_address,
             agent_port=request.instance.agent_port,
             start=start,
             end=end)) \
        .fetchall()
    statements = [dict(statement) for statement in statements]
    return jsonify(dict(data=statements))


@blueprint.instance_route(r'/statements/data/(.*)')
def json_data_database(request, database):
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)

    query = """
        SELECT
          sum((record).blk_read_time) AS blk_read_time,
          sum((record).blk_write_time) AS blk_write_time,
          sum((record).calls) AS calls,
          sum((record).local_blks_dirtied) AS local_blks_dirtied,
          sum((record).local_blks_hit) AS local_blks_hit,
          sum((record).local_blks_read) AS local_blks_read,
          sum((record).local_blks_written) AS local_blks_written,
          max((record).max_time) AS max_time,
          sum((record).total_time) / sum((record).calls) AS mean_time,
          min((record).min_time) AS min_time,
          statements.query,
          statements.rolname,
          sum((record).rows) AS rows,
          sum((record).shared_blks_dirtied) AS shared_blks_dirtied,
          sum((record).shared_blks_hit) AS shared_blks_hit,
          sum((record).shared_blks_read) AS shared_blks_read,
          sum((record).shared_blks_written) AS shared_blks_written,
          sum((record).stddev_time) AS stddev_time,
          sum((record).temp_blks_read) AS temp_blks_read,
          sum((record).temp_blks_written) AS temp_blks_written,
          sum((record).total_time) AS total_time
        FROM statements.statements_history_current AS history
        JOIN statements.statements AS statements ON (
          history.agent_address = statements.agent_address AND
          history.agent_port = statements.agent_port AND
          history.queryid = statements.queryid AND
          history.dbid = statements.dbid AND
          history.userid = statements.userid
        )
        WHERE statements.agent_address = :agent_address
        AND statements.agent_port = :agent_port
        AND statements.datname = :database
        AND history.datetime <@ tstzrange(:start, :end, '[]')
        GROUP BY statements.query,
                 statements.datname,
                 statements.rolname
    """
    statements = request.db_session.execute(
        query,
        dict(agent_address=request.instance.agent_address,
             agent_port=request.instance.agent_port,
             database=database,
             start=start,
             end=end)) \
        .fetchall()
    statements = [dict(statement) for statement in statements]
    return jsonify(dict(data=statements))


@blueprint.instance_route(r'/statements')
def statements(request):
    request.instance.check_active_plugin(__name__)
    return render_template(
        'index.html',
        nav=True,
        agent_username=get_agent_username(request),
        instance=request.instance,
        plugin=__name__,
        role=request.current_user,
    )


def add_statement(session, instance, data):
    try:
        for statement in data.get('data'):
            cur = session.connection().connection.cursor()
            query = """
                INSERT INTO statements.statements
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """
            cur.execute(
                query,
                (
                    instance.agent_address,
                    instance.agent_port,
                    statement['queryid'],
                    statement['query'],
                    statement['dbid'],
                    statement['datname'],
                    statement['userid'],
                    statement['rolname'],
                ),
            )
            query = """
                INSERT INTO statements.statements_history_current
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
            cur.execute(
                query,
                (
                    data['snapshot_datetime'],
                    instance.agent_address,
                    instance.agent_port,
                    statement['queryid'],
                    statement['dbid'],
                    statement['userid'],
                    (
                        statement['blk_read_time'],
                        statement['blk_write_time'],
                        statement['calls'],
                        statement['local_blks_hit'],
                        statement['local_blks_read'],
                        statement['local_blks_dirtied'],
                        statement['local_blks_written'],
                        statement['max_time'],
                        statement['mean_time'],
                        statement['min_time'],
                        statement['rows'],
                        statement['shared_blks_hit'],
                        statement['shared_blks_read'],
                        statement['shared_blks_dirtied'],
                        statement['shared_blks_written'],
                        statement['stddev_time'],
                        statement['temp_blks_read'],
                        statement['temp_blks_written'],
                        statement['total_time'],
                    )
                )
            )
        session.connection().connection.commit()
    except Exception as e:
        raise TemboardUIError(400, e.message)


@workers.register(pool_size=1)
def pull_data_worker(app):
    # Worker in charge of retrieving statements data
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
    instances = worker_session.query(Instances)

    for instance in instances:
        plugin_names = [plugin.plugin_name for plugin in instance.plugins]

        if 'statements' not in plugin_names:
            continue

        # FIXME should be done in parallel
        try:
            pull_data_for_instance(app, worker_session, instance)
        except Exception:
            pass


def pull_data_for_instance(app, session, instance):
    try:
        instance = session.query(Instances).filter(
            Instances.pg_port == 5432,
            Instances.hostname == 'instance.fqdn',
        ).one()
        url = 'https://%s:%s%s?key=%s' % (
            instance.agent_address,
            instance.agent_port,
            '/statements',
            instance.agent_key,
        )
        headers = {}
        try:
            body = temboard_request(
                app.config.temboard.ssl_ca_cert_file,
                method='GET',
                url=url,
                headers=headers,
            )
        except urllib2.HTTPError as e:
            message = e.read()
            try:
                message = json_decode(message)['error']
            except Exception as ee:
                logger.debug("Failed to decode agent error: %s.", ee)
            raise HTTPError(e.code, message)
        except urllib2.URLError as e:
            logger.error("Proxied request failed: %s", e)
            raise HTTPError(500, str(e.reason))
        except Exception as e:
            logger.error("Proxied request failed: %s", e)
            raise HTTPError(500)
        add_statement(session, instance, json_decode(body))
    except Exception as e:
        logger.error('Could not get statements data')
        logger.exception(e)
        raise(e)


@taskmanager.bootstrap()
def statements_bootstrap(context):
    yield taskmanager.Task(
        worker_name='pull_data_worker',
        id='statementsdata',
        redo_interval=1 * 60,  # Repeat each 1m,
        options={},
    )
