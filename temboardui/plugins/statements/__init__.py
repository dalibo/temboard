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
from sqlalchemy.sql import (
    column,
    extract,
    func,
    select,
    text,
)
from temboardui.model.orm import (
    Biggest,
    Biggestsum,
    Instances,
    diff,
    to_epoch,
    total_hit,
    total_read,
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

PLUGIN_NAME = 'statements'

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


BASE_QUERY_STATDATA = text("""
    (
        SELECT
          dbid,
          datname,
          (record).*
        FROM statements.statements_history_current_db
        WHERE agent_address = :agent_address
        AND agent_port = :agent_port
        AND tstzrange((record).ts, (record).ts, '[]')
          <@ tstzrange(:start, :end, '[]')
    ) h
""")


@blueprint.instance_route(r'/statements/data')
def json_data(request):
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)

    base_query = BASE_QUERY_STATDATA
    diffs = get_diffs_forstatdata()
    query = (select([
        column("datname"),
    ] + diffs)
            .select_from(base_query)
            .group_by(column("dbid"), column("datname"))
            .having(func.max(column("calls")) - func.min(column("calls")) > 0))

    statements = request.db_session.execute(
        query,
        dict(agent_address=request.instance.agent_address,
             agent_port=request.instance.agent_port,
             start=start,
             end=end)) \
        .fetchall()
    statements = [dict(statement) for statement in statements]
    return jsonify(dict(data=statements))


BASE_QUERY_STATDATA_DATABASE = text("""
    (
        SELECT
          statements.*,
          (record).*
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
        AND tstzrange((record).ts, (record).ts, '[]')
          <@ tstzrange(:start, :end, '[]')
    ) h
""")


@blueprint.instance_route(r'/statements/data/(.*)')
def json_data_database(request, database):
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)

    base_query = BASE_QUERY_STATDATA_DATABASE
    diffs = get_diffs_forstatdata()
    query = (select([
        column("query"),
        column("datname"),
        column("rolname"),
    ] + diffs)
            .select_from(base_query)
            .group_by(column("query"), column("dbid"), column("datname"),
                      column("rolname"))
            .having(func.max(column("calls")) - func.min(column("calls")) > 0))

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


def get_diffs_forstatdata():
    return [
        diff("calls"),
        diff("total_time").label("total_time"),
        (diff("total_time") / diff("calls")).label("mean_time"),
        diff("shared_blks_read"),
        diff("shared_blks_hit"),
        diff("shared_blks_dirtied"),
        diff("shared_blks_written"),
        diff("local_blks_read"),
        diff("local_blks_hit"),
        diff("local_blks_dirtied"),
        diff("local_blks_written"),
        diff("temp_blks_read"),
        diff("temp_blks_written"),
        diff("blk_read_time"),
        diff("blk_write_time")
    ]


BASE_QUERY_STATDATA_SAMPLE_INSTANCE = text("""
    (
      SELECT *
      FROM (
        SELECT
          row_number() OVER (ORDER BY ts) AS number,
          count(*) OVER (PARTITION BY 1) AS total,
          *
        FROM (
          SELECT
            (record).ts,
            sum((record).calls) AS calls,
            sum((record).total_time) AS total_time,
            sum((record).rows) AS rows,
            sum((record).shared_blks_hit) AS shared_blks_hit,
            sum((record).shared_blks_read) AS shared_blks_read,
            sum((record).shared_blks_dirtied) AS shared_blks_dirtied,
            sum((record).shared_blks_written) AS shared_blks_written,
            sum((record).local_blks_hit) AS local_blks_hit,
            sum((record).local_blks_read) AS local_blks_read,
            sum((record).local_blks_dirtied) AS local_blks_dirtied,
            sum((record).local_blks_written) AS local_blks_written,
            sum((record).temp_blks_read) AS temp_blks_read,
            sum((record).temp_blks_written) AS temp_blks_written,
            sum((record).blk_read_time) AS blk_read_time,
            sum((record).blk_write_time) AS blk_write_time
          FROM statements.statements_history_current_db
          WHERE tstzrange((record).ts, (record).ts, '[]')
            <@ tstzrange(:start, :end, '[]')
          AND agent_address = :agent_address
          AND agent_port = :agent_port
          GROUP BY (record).ts
        ) AS statements_history
      ) AS sh
      WHERE number % ( int8larger((total)/(:samples +1),1) ) = 0
    ) by_instance
""")


BASE_QUERY_STATDATA_SAMPLE_DATABASE = text("""
    (
      SELECT *
      FROM (
        SELECT
          row_number() OVER (ORDER BY ts) AS number,
          count(*) OVER (PARTITION BY 1) AS total,
          *
        FROM (
          SELECT (record).*
          FROM statements.statements_history_current_db
          WHERE tstzrange((record).ts, (record).ts, '[]')
            <@ tstzrange(:start, :end, '[]')
          AND datname = :datname
          AND agent_address = :agent_address
          AND agent_port = :agent_port
        ) AS statements_history
      ) AS sh
      WHERE number % ( int8larger((total)/(:samples +1),1) ) = 0
    ) by_db
""")


def getstatdata_sample(request, mode, start, end, database=None):
    if mode == 'instance':
        base_query = BASE_QUERY_STATDATA_SAMPLE_INSTANCE

    elif mode == "db":
        base_query = BASE_QUERY_STATDATA_SAMPLE_DATABASE

    elif mode == "query":
        pass

    ts = column('ts')
    biggest = Biggest(ts)
    biggestsum = Biggestsum(ts)

    subquery = (select([
        ts,
        biggest("ts", '0 s', "mesure_interval"),
        biggestsum("calls"),
        biggestsum("total_time", label="runtime"),
        biggestsum("rows"),
        biggestsum("shared_blks_read"),
        biggestsum("shared_blks_hit"),
        biggestsum("shared_blks_dirtied"),
        biggestsum("shared_blks_written"),
        biggestsum("local_blks_read"),
        biggestsum("local_blks_hit"),
        biggestsum("local_blks_dirtied"),
        biggestsum("local_blks_written"),
        biggestsum("temp_blks_read"),
        biggestsum("temp_blks_written"),
        biggestsum("blk_read_time"),
        biggestsum("blk_write_time")
        ])
            .select_from(base_query)
            .apply_labels()
            .group_by(*([ts])))

    subquery = subquery.alias()
    c = subquery.c

    greatest = func.greatest
    cols = [
        to_epoch(c.ts),
        (
            func.sum(c.calls) /
            greatest(extract("epoch", c.mesure_interval), 1)
        ).label("calls"),
        (
            func.sum(c.runtime) / greatest(func.sum(c.calls), 1.)
        ).label("avg_runtime"),
        (
            func.sum(c.runtime) /
            greatest(extract("epoch", c.mesure_interval), 1)
        ).label("load"),
        total_read(c),
        total_hit(c)
    ]

    query = (
        select(cols)
        .select_from(subquery)
        .where(c.calls is not None)
        .group_by(c.ts, c.mesure_interval)
        .order_by(c.ts)
    )

    params = dict(agent_address=request.instance.agent_address,
                  agent_port=request.instance.agent_port,
                  samples=50,
                  start=start,
                  end=end)

    if mode == 'db':
        params['datname'] = database

    rows = request.db_session.execute(query, params).fetchall()
    return [dict(row) for row in rows]


@blueprint.instance_route(r'/statements/chart')
def json_chart_data_instance(request):
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)

    data = getstatdata_sample(request, "instance", start, end)
    return jsonify(dict(data=data))


@blueprint.instance_route(r'/statements/chart/(.*)')
def json_chart_data_db(request, database):
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)

    data = getstatdata_sample(request, "db", start, end, database=database)
    return jsonify(dict(data=data))


@blueprint.instance_route(r'/statements')
def statements(request):
    request.instance.check_active_plugin(PLUGIN_NAME)
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
        cur = session.connection().connection.cursor()
        for statement in data.get('data'):
            query = """
                INSERT INTO statements.statements_src_tmp
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(
                query,
                (
                    instance.agent_address,
                    instance.agent_port,
                    data['snapshot_datetime'],
                    statement['userid'],
                    statement['rolname'],
                    statement['dbid'],
                    statement['datname'],
                    statement['queryid'],
                    statement['query'],
                    statement['calls'],
                    statement['total_time'],
                    statement['rows'],
                    statement['shared_blks_hit'],
                    statement['shared_blks_read'],
                    statement['shared_blks_dirtied'],
                    statement['shared_blks_written'],
                    statement['local_blks_hit'],
                    statement['local_blks_read'],
                    statement['local_blks_dirtied'],
                    statement['local_blks_written'],
                    statement['temp_blks_read'],
                    statement['temp_blks_written'],
                    statement['blk_read_time'],
                    statement['blk_write_time']
                )
            )
        query = """SELECT statements.process_statements(%s, %s)"""
        cur.execute(query, (instance.agent_address, instance.agent_port))
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
