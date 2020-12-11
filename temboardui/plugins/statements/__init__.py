import json
import logging
from os import path
import tornado.web
from tornado.escape import json_decode

from sqlalchemy.orm import (
    sessionmaker,
    scoped_session,
)
from sqlalchemy.sql import (
    column,
    extract,
    func,
    select,
    text,
)
from temboardui.model import worker_engine
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


METAS_QUERY = text("""
    SELECT *
    FROM statements.metas
    WHERE agent_address = :agent_address
    AND agent_port = :agent_port
""")


BASE_QUERY_STATDATA = text("""
    (
        SELECT dbid, datname, (record).*
        FROM (
          SELECT psh.dbid, psh.datname, unnest(records) AS record
          FROM statements.statements_history_db psh
          WHERE coalesce_range && tstzrange(:start, :end,'[]')
          AND    agent_address = :agent_address
          AND    agent_port = :agent_port
        ) AS unnested
        WHERE tstzrange((record).ts, (record).ts, '[]')
              <@ tstzrange(:start, :end, '[]')

        UNION ALL

        SELECT dbid, datname, (record).*
        FROM statements.statements_history_current_db
        WHERE agent_address = :agent_address
        AND agent_port = :agent_port
        AND tstzrange((record).ts, (record).ts, '[]')
          <@ tstzrange(:start, :end, '[]')
    ) h
""")


@blueprint.instance_route(r'/statements/data')
def json_data_instance(request):
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)

    base_query = BASE_QUERY_STATDATA
    diffs = get_diffs_forstatdata()
    query = (select([
        column("datname"),
        column("dbid"),
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

    metas = request.db_session.execute(
        METAS_QUERY,
        dict(agent_address=request.instance.agent_address,
             agent_port=request.instance.agent_port)).fetchone()
    metas = dict(metas) if metas is not None else None
    return jsonify(dict(data=statements, metas=metas))


BASE_QUERY_STATDATA_DATABASE = """
WITH first_occurence AS (
  -- first occurence for each statement
  SELECT
    distinct on (queryid, userid)
    queryid,
    userid,
    ts,
    calls,
    total_exec_time,
    shared_blks_read,
    shared_blks_hit,
    shared_blks_dirtied,
    shared_blks_written,
    local_blks_read,
    local_blks_hit,
    local_blks_dirtied,
    local_blks_written,
    temp_blks_read,
    temp_blks_written,
    blk_read_time,
    blk_write_time
  FROM
    (
      (
        SELECT
          distinct on (queryid, userid)
          queryid,
          userid,
          (record).*
        FROM
          (
            SELECT
              distinct on (queryid, userid)
              queryid,
              userid,
              unnest(records) AS record
            FROM
              statements.statements_history psh
            WHERE
              coalesce_range && tstzrange(
                (:start) :: timestamptz,
                (:end) :: timestamptz,
                '[]'
              )
              AND agent_address = :agent_address
              AND agent_port = :agent_port
              AND dbid = :dbid
              {queryidfilter}
            order by
              queryid,
              userid,
              coalesce_range
          ) AS unnested
        WHERE
          tstzrange(
            (record).ts,
            (record).ts,
            '[]'
          ) <@ tstzrange(
            (:start) :: timestamptz,
            (:end) :: timestamptz,
            '[]'
          )
        order by
          queryid,
          userid,
          ts
      )
      UNION ALL
        (
          SELECT
            distinct on (queryid, userid)
            queryid,
            userid,
            (record).*
          FROM
            statements.statements_history_current
          WHERE
            agent_address = :agent_address
            AND agent_port = :agent_port
            AND dbid = :dbid
            AND tstzrange(
              (record).ts,
              (record).ts,
              '[]'
            ) <@ tstzrange(
              (:start) :: timestamptz,
              (:end) :: timestamptz,
              '[]'
            )
            {queryidfilter}
          order by
            queryid,
            userid,
            ts
        )
    ) as h
  order by
    queryid,
    userid,
    ts
),
last_occurence AS (
  -- last occurence for each statement
  SELECT
    distinct on (queryid, userid)
    queryid,
    userid,
    ts,
    calls,
    total_exec_time,
    shared_blks_read,
    shared_blks_hit,
    shared_blks_dirtied,
    shared_blks_written,
    local_blks_read,
    local_blks_hit,
    local_blks_dirtied,
    local_blks_written,
    temp_blks_read,
    temp_blks_written,
    blk_read_time,
    blk_write_time
  FROM
    (
      (
        SELECT
          distinct on (queryid, userid)
          queryid,
          userid,
          (record).*
        FROM
          (
            SELECT
              distinct on (queryid, userid)
              queryid,
              userid,
              unnest(records) AS record
            FROM
              statements.statements_history psh
            WHERE
              coalesce_range && tstzrange(
                (:start) :: timestamptz,
                (:end) :: timestamptz,
                '[]'
              )
              AND agent_address = :agent_address
              AND agent_port = :agent_port
              AND dbid = :dbid
              {queryidfilter}
            order by
              queryid,
              userid,
              coalesce_range desc
          ) AS unnested
        WHERE
          tstzrange(
            (record).ts,
            (record).ts,
            '[]'
          ) <@ tstzrange(
            (:start) :: timestamptz,
            (:end) :: timestamptz,
            '[]'
          )
        order by
          queryid,
          userid,
          ts desc
      )
      UNION ALL
        (
          SELECT
            distinct on (queryid, userid)
            queryid,
            userid,
            (record).*
          FROM
            statements.statements_history_current
          WHERE
            agent_address = :agent_address
            AND agent_port = :agent_port
            AND dbid = :dbid
            AND tstzrange(
              (record).ts,
              (record).ts,
              '[]'
            ) <@ tstzrange(
              (:start) :: timestamptz,
              (:end) :: timestamptz,
              '[]'
            )
            {queryidfilter}
          order by
            queryid,
            userid,
            ts desc
        )
    ) as h
  order by
    queryid,
    userid,
    ts desc
)
SELECT
  query,
  statements.queryid::text,
  rolname,
  statements.userid::text,
  (lo.calls - fo.calls) AS calls,
  (lo.total_exec_time - fo.total_exec_time) AS total_exec_time,
  (lo.total_exec_time - fo.total_exec_time) /
    (lo.calls - fo.calls) AS mean_time,
  (
    lo.shared_blks_read - fo.shared_blks_read
  ) AS shared_blks_read,
  (
    lo.shared_blks_hit - fo.shared_blks_hit
  ) AS shared_blks_hit,
  (
    lo.shared_blks_dirtied - fo.shared_blks_dirtied
  ) AS shared_blks_dirtied,
  (
    lo.shared_blks_written - fo.shared_blks_written
  ) AS shared_blks_written,
  (
    lo.local_blks_read - fo.local_blks_read
  ) AS local_blks_read,
  (
    lo.local_blks_hit - fo.local_blks_hit
  ) AS local_blks_hit,
  (
    lo.local_blks_dirtied - fo.local_blks_dirtied
  ) AS local_blks_dirtied,
  (
    lo.local_blks_written - fo.local_blks_written
  ) AS local_blks_written,
  (
    lo.temp_blks_read - fo.temp_blks_read
  ) AS temp_blks_read,
  (
    lo.temp_blks_written - fo.temp_blks_written
  ) AS temp_blks_written,
  (
    lo.blk_read_time - fo.blk_read_time
  ) AS blk_read_time,
  (
    lo.blk_write_time - fo.blk_write_time
  ) AS blk_write_time
FROM
  first_occurence AS fo
  JOIN last_occurence AS lo
    ON fo.queryid = lo.queryid
    AND fo.userid = lo.userid
  JOIN statements.statements
    ON statements.queryid = fo.queryid
    AND statements.userid = fo.userid
  AND agent_address = :agent_address
  AND agent_port = :agent_port
  AND dbid = :dbid
WHERE (lo.calls - fo.calls) > 0;
"""


@blueprint.instance_route(r'/statements/data/([0-9]*)/([-]?[0-9]*)/([0-9]*)')
def json_data_query(request, dbid, queryid, userid):
    return json_data(request, dbid, queryid, userid)


@blueprint.instance_route(r'/statements/data/(.*)')
def json_data_database(request, dbid):
    return json_data(request, dbid)


def json_data(request, dbid, queryid=None, userid=None):
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)

    query = text("""
        SELECT DISTINCT(datname)
        FROM statements.statements
        WHERE dbid = :dbid
        AND agent_address = :agent_address
        AND agent_port = :agent_port;
    """)
    datname = request.db_session.execute(
        query,
        dict(agent_address=request.instance.agent_address,
             agent_port=request.instance.agent_port,
             dbid=dbid)
    ).fetchone()[0]

    params = dict(agent_address=request.instance.agent_address,
                  agent_port=request.instance.agent_port,
                  dbid=dbid,
                  start=start,
                  end=end)

    query = BASE_QUERY_STATDATA_DATABASE
    queryidfilter = ''
    if queryid is not None and userid is not None:
        queryidfilter = 'AND queryid = :queryid AND userid = :userid'
        params.update(dict(queryid=queryid, userid=userid))
    query = query.format(**dict(queryidfilter=queryidfilter))

    statements = request.db_session.execute(query, params).fetchall()
    statements = [dict(statement) for statement in statements]
    return jsonify(dict(datname=datname, data=statements))


def get_diffs_forstatdata():
    return [
        diff("calls"),
        diff("total_exec_time").label("total_exec_time"),
        (diff("total_exec_time") / diff("calls")).label("mean_time"),
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
            ts,
            sum(calls) AS calls,
            sum(total_exec_time) AS total_exec_time,
            sum(rows) AS rows,
            sum(shared_blks_hit) AS shared_blks_hit,
            sum(shared_blks_read) AS shared_blks_read,
            sum(shared_blks_dirtied) AS shared_blks_dirtied,
            sum(shared_blks_written) AS shared_blks_written,
            sum(local_blks_hit) AS local_blks_hit,
            sum(local_blks_read) AS local_blks_read,
            sum(local_blks_dirtied) AS local_blks_dirtied,
            sum(local_blks_written) AS local_blks_written,
            sum(temp_blks_read) AS temp_blks_read,
            sum(temp_blks_written) AS temp_blks_written,
            sum(blk_read_time) AS blk_read_time,
            sum(blk_write_time) AS blk_write_time
          FROM (
            SELECT (record).*
            FROM (
              SELECT psh.dbid, psh.coalesce_range, unnest(records) AS record
              FROM statements.statements_history_db psh
              WHERE coalesce_range && tstzrange(:start, :end,'[]')
              AND    agent_address = :agent_address
              AND    agent_port = :agent_port
            ) AS unnested
            WHERE tstzrange((record).ts, (record).ts, '[]')
                  <@ tstzrange(:start, :end, '[]')

            UNION ALL

            SELECT (record).*
            FROM statements.statements_history_current_db
            WHERE tstzrange((record).ts, (record).ts, '[]')
              <@ tstzrange(:start, :end, '[]')
            AND agent_address = :agent_address
            AND agent_port = :agent_port
          ) AS s
          GROUP BY ts
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
          FROM (
            SELECT psh.dbid, psh.coalesce_range, unnest(records) AS record
            FROM statements.statements_history_db psh
            WHERE coalesce_range && tstzrange(:start, :end,'[]')
            AND    dbid = :dbid
            AND    agent_address = :agent_address
            AND    agent_port = :agent_port
          ) AS unnested
          WHERE tstzrange((record).ts, (record).ts, '[]')
                <@ tstzrange(:start, :end, '[]')

          UNION ALL

          SELECT (record).*
          FROM statements.statements_history_current_db
          WHERE tstzrange((record).ts, (record).ts, '[]')
            <@ tstzrange(:start, :end, '[]')
          AND dbid = :dbid
          AND agent_address = :agent_address
          AND agent_port = :agent_port
        ) AS statements_history
      ) AS sh
      WHERE number % ( int8larger((total)/(:samples +1),1) ) = 0
    ) by_db
""")

BASE_QUERY_STATDATA_SAMPLE_QUERY = text("""
    (
      SELECT *
      FROM (
        SELECT
          row_number() OVER (ORDER BY ts) AS number,
          count(*) OVER (PARTITION BY 1) AS total,
          *
        FROM (
          SELECT (record).*
          FROM (
            SELECT psh.dbid, psh.coalesce_range, unnest(records) AS record
            FROM statements.statements_history psh
            WHERE coalesce_range && tstzrange(:start, :end,'[]')
            AND dbid = :dbid
            AND queryid = :queryid
            AND userid = :userid
            AND agent_address = :agent_address
            AND agent_port = :agent_port
          ) AS unnested
          WHERE tstzrange((record).ts, (record).ts, '[]')
                <@ tstzrange(:start, :end, '[]')

          UNION ALL

          SELECT (record).*
          FROM statements.statements_history_current
          WHERE tstzrange((record).ts, (record).ts, '[]')
            <@ tstzrange(:start, :end, '[]')
          AND dbid = :dbid
          AND queryid = :queryid
          AND userid = :userid
          AND agent_address = :agent_address
          AND agent_port = :agent_port
        ) AS statements_history
      ) AS sh
      WHERE number % ( int8larger((total)/(:samples +1),1) ) = 0
    ) by_db
""")


def getstatdata_sample(request, mode, start, end, dbid=None, queryid=None,
                       userid=None):
    if mode == 'instance':
        base_query = BASE_QUERY_STATDATA_SAMPLE_INSTANCE

    elif mode == "db":
        base_query = BASE_QUERY_STATDATA_SAMPLE_DATABASE

    elif mode == "query":
        base_query = BASE_QUERY_STATDATA_SAMPLE_QUERY

    ts = column('ts')
    biggest = Biggest(ts)
    biggestsum = Biggestsum(ts)

    subquery = (select([
        ts,
        biggest("ts", '0 s', "mesure_interval"),
        biggestsum("calls"),
        biggestsum("total_exec_time", label="runtime"),
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
        .where(c.calls != 0)
        .group_by(c.ts, c.mesure_interval)
        .order_by(c.ts)
    )

    params = dict(agent_address=request.instance.agent_address,
                  agent_port=request.instance.agent_port,
                  samples=50,
                  start=start,
                  end=end)

    if mode == 'db' or mode == 'query':
        params['dbid'] = dbid
    if mode == 'query':
        params['queryid'] = queryid
        params['userid'] = userid

    rows = request.db_session.execute(query, params).fetchall()
    return [dict(row) for row in rows]


@blueprint.instance_route(r'/statements/chart')
def json_chart_data_instance(request):
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)

    data = getstatdata_sample(request, "instance", start, end)
    return jsonify(dict(data=data))


@blueprint.instance_route(r'/statements/chart/([0-9]*)/([-]?[0-9]*)/([0-9]*)')
def json_chart_data_query(request, dbid, queryid, userid):
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)

    data = getstatdata_sample(request, "query", start, end, dbid=dbid,
                              queryid=queryid, userid=userid)
    return jsonify(dict(data=data))


@blueprint.instance_route(r'/statements/chart/(.*)')
def json_chart_data_db(request, dbid):
    host_id, instance_id = get_request_ids(request)
    start, end = parse_start_end(request)

    data = getstatdata_sample(request, "db", start, end, dbid=dbid)
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
        cur.execute("SET search_path TO statements")
        for statement in data.get('data'):
            query = """
                INSERT INTO statements_src_tmp
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    statement['total_exec_time']
                    if 'total_exec_time' in statement
                    else statement['total_time'],
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
                    statement['blk_write_time'],
                    statement['total_plan_time']
                    if 'total_plan_time' in statement
                    else None,
                    statement['wal_records']
                    if 'wal_records' in statement
                    else None,
                    statement['wal_fpi']
                    if 'wal_fpi' in statement
                    else None,
                    statement['wal_bytes']
                    if 'wal_bytes' in statement
                    else None,
                )
            )
        query = """SELECT process_statements(%s, %s)"""
        cur.execute(query, (instance.agent_address, instance.agent_port))
        session.connection().connection.commit()
    except Exception as e:
        raise TemboardUIError(400, e.message)


@workers.register(pool_size=1)
def pull_data_worker(app):
    engine = worker_engine(app.config.repository)
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
        add_statement(session, instance, json_decode(body))
    except Exception as e:
        error = 'Error while fetching statements from instance: '
        if hasattr(e, 'read'):
            error += json.loads(e.read())['error']
        else:
            error += str(e)

        logger.error(error)
        logger.exception(e)

        # If statements data cannot be retrieved store the error in the
        # statements metas table
        cur = session.connection().connection.cursor()
        cur.execute("SET search_path TO statements")
        query = """
            -- Create new meta for agent if doesn't already exist
            INSERT INTO metas (agent_address, agent_port)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """
        cur.execute(
            query,
            (
                instance.agent_address,
                instance.agent_port,
            )
        )

        query = """
            UPDATE metas
            SET error = %s
            WHERE agent_address = %s AND agent_port = %s;
        """
        cur.execute(
            query,
            (
                error,
                instance.agent_address,
                instance.agent_port,
            )
        )
        session.connection().connection.commit()
        raise(e)


@workers.register(pool_size=1)
def purge_data_worker(app):
    """Background worker in charge of purging statements data.
    Purge policy is based on purge_after parameter from statements section.
    purge_after sets the number of days of data to keep, from now. Default is
    7 days if not set.
    """
    logger.setLevel(app.config.logging.level)
    logger.info("Purging old statements data")

    engine = worker_engine(app.config.repository)
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    session = Session()

    purge_after = app.config.statements.purge_after

    # Get tablename list to purge from metric_tables_config()
    try:
        cur = session.connection().connection.cursor()
        cur.execute("SET search_path TO statements")
        cur.execute("""SELECT statements_purge(%s)""", (purge_after,))
        session.connection().connection.commit()
    except Exception as e:
        logger.error('Could not purge statements data')
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
    yield taskmanager.Task(
        worker_name='purge_data_worker',
        id='purge_data',
        redo_interval=24 * 60 * 60,  # Repeat each 24h,
        options={},
    )
