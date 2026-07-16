import logging
from decimal import Decimal

from flask import current_app, g, jsonify, render_template
from sqlalchemy.sql import column, extract, func, select, text

from temboardui.plugins.monitoring.tools import parse_start_end_flask as parse_start_end

from ...web.flask import instance_routes
from . import Biggest, Biggestsum, diff, to_epoch, total_hit, total_read

logger = logging.getLogger(__name__)


PLUGIN_NAME = "statements"

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


@instance_routes.route("/statements/data")
def json_data_instance():
    start, end = parse_start_end()

    base_query = BASE_QUERY_STATDATA
    diffs = get_diffs_forstatdata()
    query = (
        select([column("datname"), column("dbid")] + diffs)
        .select_from(base_query)
        .group_by(column("dbid"), column("datname"))
        .having(func.max(column("calls")) - func.min(column("calls")) > 0)
    )

    statements = g.db_session.execute(
        query,
        dict(
            agent_address=g.instance.agent_address,
            agent_port=g.instance.agent_port,
            start=start,
            end=end,
        ),
    ).fetchall()
    statements = [dict(statement) for statement in statements]

    metas = g.db_session.execute(
        METAS_QUERY,
        dict(
            agent_address=g.instance.agent_address,
            agent_port=g.instance.agent_port,
        ),
    ).fetchone()
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


@instance_routes.route("/statements/data/<dbid>/<queryid>/<userid>")
def json_data_query(dbid, queryid, userid):
    return json_data(dbid, queryid, userid)


@instance_routes.route("/statements/data/<dbid>")
def json_data_database(dbid):
    return json_data(dbid)


def json_data(dbid, queryid=None, userid=None):
    start, end = parse_start_end()

    query = text("""
        SELECT DISTINCT(datname)
        FROM statements.statements
        WHERE dbid = :dbid
        AND agent_address = :agent_address
        AND agent_port = :agent_port;
    """)
    datname = g.db_session.execute(
        query,
        dict(
            agent_address=g.instance.agent_address,
            agent_port=g.instance.agent_port,
            dbid=dbid,
        ),
    ).fetchone()[0]

    params = dict(
        agent_address=g.instance.agent_address,
        agent_port=g.instance.agent_port,
        dbid=dbid,
        start=start,
        end=end,
    )

    query = BASE_QUERY_STATDATA_DATABASE
    queryidfilter = ""
    if queryid is not None and userid is not None:
        queryidfilter = "AND queryid = :queryid AND userid = :userid"
        params.update(dict(queryid=queryid, userid=userid))
    query = query.format(**dict(queryidfilter=queryidfilter))

    statements = g.db_session.execute(query, params).fetchall()
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
        diff("blk_write_time"),
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


def getstatdata_sample(mode, start, end, dbid=None, queryid=None, userid=None):
    if mode == "instance":
        base_query = BASE_QUERY_STATDATA_SAMPLE_INSTANCE

    elif mode == "db":
        base_query = BASE_QUERY_STATDATA_SAMPLE_DATABASE

    elif mode == "query":
        base_query = BASE_QUERY_STATDATA_SAMPLE_QUERY

    ts = column("ts")
    biggest = Biggest(ts)
    biggestsum = Biggestsum(ts)

    subquery = (
        select(
            [
                ts,
                biggest("ts", "0 s", "mesure_interval"),
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
                biggestsum("blk_write_time"),
            ]
        )
        .select_from(base_query)
        .apply_labels()
        .group_by(*([ts]))
    )

    subquery = subquery.alias()
    c = subquery.c

    greatest = func.greatest
    cols = [
        to_epoch(c.ts),
        (func.sum(c.calls) / greatest(extract("epoch", c.mesure_interval), 1)).label(
            "calls"
        ),
        (func.sum(c.runtime) / greatest(func.sum(c.calls), 1.0)).label("avg_runtime"),
        (func.sum(c.runtime) / greatest(extract("epoch", c.mesure_interval), 1)).label(
            "load"
        ),
        total_read(c),
        total_hit(c),
    ]

    query = (
        select(cols)
        .select_from(subquery)
        .where(c.calls != 0)
        .group_by(c.ts, c.mesure_interval)
        .order_by(c.ts)
    )

    params = dict(
        agent_address=g.instance.agent_address,
        agent_port=g.instance.agent_port,
        samples=50,
        start=start,
        end=end,
    )

    if mode == "db" or mode == "query":
        params["dbid"] = dbid
    if mode == "query":
        params["queryid"] = queryid
        params["userid"] = userid

    rows = g.db_session.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def convert_decimal_to_float(data):
    # Since Postgres 14, timestamp and other data are returned as Decimal
    # rather than float. stock json does not know how to serialize Decimals.
    # For now, just preprocess data to convert decimals to float in payload
    # before serializing to json.
    if isinstance(data, Decimal):
        return float(data)
    elif isinstance(data, list):
        return [convert_decimal_to_float(v) for v in data]
    elif isinstance(data, dict):
        return {k: convert_decimal_to_float(v) for k, v in data.items()}
    else:
        return data


@instance_routes.route("/statements/chart")
def json_chart_data_instance():
    start, end = parse_start_end()

    data = getstatdata_sample("instance", start, end)
    data = convert_decimal_to_float(data)
    return jsonify(dict(data=data))


@instance_routes.route("/statements/chart/<dbid>/<queryid>/<userid>")
def json_chart_data_query(dbid, queryid, userid):
    start, end = parse_start_end()

    data = getstatdata_sample(
        "query", start, end, dbid=dbid, queryid=queryid, userid=userid
    )
    data = convert_decimal_to_float(data)
    return jsonify(dict(data=data))


@instance_routes.route("/statements/chart/<dbid>")
def json_chart_data_db(dbid):
    start, end = parse_start_end()

    data = getstatdata_sample("db", start, end, dbid=dbid)
    data = convert_decimal_to_float(data)
    return jsonify(dict(data=data))


@instance_routes.route("/statements")
def statements():
    current_app.instance.check_active_plugin(PLUGIN_NAME)
    current_app.instance.fetch_status()
    return render_template(
        "statements/index.html",
        instance=g.instance,
        plugin=PLUGIN_NAME,
        role=g.current_user,
    )
