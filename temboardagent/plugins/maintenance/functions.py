from datetime import datetime, timedelta
import hashlib
import logging
import os

from temboardagent.errors import UserError, HTTPError
from temboardagent.postgres import Postgres
from temboardagent.spc import error
from temboardagent.toolkit import taskmanager

logger = logging.getLogger(__name__)

# Taken from https://github.com/ioguix/pgsql-bloat-estimation/blob/master/table/table_bloat.sql  # noqa
TABLE_BLOAT_SQL = """
SELECT current_database(), schemaname, tblname, bs*tblpages AS real_size,
  (tblpages-est_tblpages)*bs AS extra_size,
  CASE WHEN tblpages - est_tblpages > 0
    THEN 100 * (tblpages - est_tblpages)/tblpages::float
    ELSE 0
  END AS extra_ratio, fillfactor,
  CASE WHEN tblpages - est_tblpages_ff > 0
    THEN (tblpages-est_tblpages_ff)*bs
    ELSE 0
  END AS bloat_size,
  CASE WHEN tblpages - est_tblpages_ff > 0
    THEN 100 * (tblpages - est_tblpages_ff)/tblpages::float
    ELSE 0
  END AS bloat_ratio, is_na
  -- , (pst).free_percent + (pst).dead_tuple_percent AS real_frag
FROM (
  SELECT ceil( reltuples / ( (bs-page_hdr)/tpl_size ) ) + ceil( toasttuples / 4 ) AS est_tblpages,
    ceil( reltuples / ( (bs-page_hdr)*fillfactor/(tpl_size*100) ) ) + ceil( toasttuples / 4 ) AS est_tblpages_ff,
    tblpages, fillfactor, bs, tblid, schemaname, tblname, heappages, toastpages, is_na
    -- , stattuple.pgstattuple(tblid) AS pst
  FROM (
    SELECT
      ( 4 + tpl_hdr_size + tpl_data_size + (2*ma)
        - CASE WHEN tpl_hdr_size%ma = 0 THEN ma ELSE tpl_hdr_size%ma END
        - CASE WHEN ceil(tpl_data_size)::int%ma = 0 THEN ma ELSE ceil(tpl_data_size)::int%ma END
      ) AS tpl_size, bs - page_hdr AS size_per_block, (heappages + toastpages) AS tblpages, heappages,
      toastpages, reltuples, toasttuples, bs, page_hdr, tblid, schemaname, tblname, fillfactor, is_na
    FROM (
      SELECT
        tbl.oid AS tblid, ns.nspname AS schemaname, tbl.relname AS tblname, tbl.reltuples,
        tbl.relpages AS heappages, coalesce(toast.relpages, 0) AS toastpages,
        coalesce(toast.reltuples, 0) AS toasttuples,
        coalesce(substring(
          array_to_string(tbl.reloptions, ' ')
          FROM 'fillfactor=([0-9]+)')::smallint, 100) AS fillfactor,
        current_setting('block_size')::numeric AS bs,
        CASE WHEN version()~'mingw32' OR version()~'64-bit|x86_64|ppc64|ia64|amd64' THEN 8 ELSE 4 END AS ma,
        24 AS page_hdr,
        23 + CASE WHEN MAX(coalesce(s.null_frac,0)) > 0 THEN ( 7 + count(s.attname) ) / 8 ELSE 0::int END
           + CASE WHEN bool_or(att.attname = 'oid' and att.attnum < 0) THEN 4 ELSE 0 END AS tpl_hdr_size,
        sum( (1-coalesce(s.null_frac, 0)) * coalesce(s.avg_width, 0) ) AS tpl_data_size,
        bool_or(att.atttypid = 'pg_catalog.name'::regtype)
          OR sum(CASE WHEN att.attnum > 0 THEN 1 ELSE 0 END) <> count(s.attname) AS is_na
      FROM pg_attribute AS att
        JOIN pg_class AS tbl ON att.attrelid = tbl.oid
        JOIN pg_namespace AS ns ON ns.oid = tbl.relnamespace
        LEFT JOIN pg_stats AS s ON s.schemaname=ns.nspname
          AND s.tablename = tbl.relname AND s.inherited=false AND s.attname=att.attname
        LEFT JOIN pg_class AS toast ON tbl.reltoastrelid = toast.oid
      WHERE NOT att.attisdropped
        AND tbl.relkind = 'r'
      GROUP BY 1,2,3,4,5,6,7,8,9,10
      ORDER BY 2,3
    ) AS s
  ) AS s2
) AS s3
"""  # noqa


INDEX_BTREE_BLOAT_SQL = """
-- This query must be exected by a superuser because it relies on the
-- pg_statistic table.
-- This query run much faster than btree_bloat.sql, about 1000x faster.
--
-- This query is compatible with PostgreSQL 8.2 and after.
SELECT current_database(), nspname AS schemaname, tblname, idxname, bs*(relpages)::bigint AS real_size,
  bs*(relpages-est_pages)::bigint AS extra_size,
  100 * (relpages-est_pages)::float / relpages AS extra_ratio,
  fillfactor,
  CASE WHEN relpages > est_pages_ff
    THEN bs*(relpages-est_pages_ff)
    ELSE 0
  END AS bloat_size,
  100 * (relpages-est_pages_ff)::float / relpages AS bloat_ratio,
  is_na
  -- , 100-(pst).avg_leaf_density AS pst_avg_bloat, est_pages, index_tuple_hdr_bm, maxalign, pagehdr, nulldatawidth, nulldatahdrwidth, reltuples, relpages -- (DEBUG INFO)
FROM (
  SELECT coalesce(1 +
         ceil(reltuples/floor((bs-pageopqdata-pagehdr)/(4+nulldatahdrwidth)::float)), 0 -- ItemIdData size + computed avg size of a tuple (nulldatahdrwidth)
      ) AS est_pages,
      coalesce(1 +
         ceil(reltuples/floor((bs-pageopqdata-pagehdr)*fillfactor/(100*(4+nulldatahdrwidth)::float))), 0
      ) AS est_pages_ff,
      bs, nspname, tblname, idxname, relpages, fillfactor, is_na
      -- , pgstatindex(idxoid) AS pst, index_tuple_hdr_bm, maxalign, pagehdr, nulldatawidth, nulldatahdrwidth, reltuples -- (DEBUG INFO)
  FROM (
      SELECT maxalign, bs, nspname, tblname, idxname, reltuples, relpages, idxoid, fillfactor,
            ( index_tuple_hdr_bm +
                maxalign - CASE -- Add padding to the index tuple header to align on MAXALIGN
                  WHEN index_tuple_hdr_bm%maxalign = 0 THEN maxalign
                  ELSE index_tuple_hdr_bm%maxalign
                END
              + nulldatawidth + maxalign - CASE -- Add padding to the data to align on MAXALIGN
                  WHEN nulldatawidth = 0 THEN 0
                  WHEN nulldatawidth::integer%maxalign = 0 THEN maxalign
                  ELSE nulldatawidth::integer%maxalign
                END
            )::numeric AS nulldatahdrwidth, pagehdr, pageopqdata, is_na
            -- , index_tuple_hdr_bm, nulldatawidth -- (DEBUG INFO)
      FROM (
          SELECT n.nspname, ct.relname AS tblname, i.idxname, i.reltuples, i.relpages,
              i.idxoid, i.fillfactor, current_setting('block_size')::numeric AS bs,
              CASE -- MAXALIGN: 4 on 32bits, 8 on 64bits (and mingw32 ?)
                WHEN version() ~ 'mingw32' OR version() ~ '64-bit|x86_64|ppc64|ia64|amd64' THEN 8
                ELSE 4
              END AS maxalign,
              /* per page header, fixed size: 20 for 7.X, 24 for others */
              24 AS pagehdr,
              /* per page btree opaque data */
              16 AS pageopqdata,
              /* per tuple header: add IndexAttributeBitMapData if some cols are null-able */
              CASE WHEN max(coalesce(s.stanullfrac,0)) = 0
                  THEN 2 -- IndexTupleData size
                  ELSE 2 + (( 32 + 8 - 1 ) / 8) -- IndexTupleData size + IndexAttributeBitMapData size ( max num filed per index + 8 - 1 /8)
              END AS index_tuple_hdr_bm,
              /* data len: we remove null values save space using it fractionnal part from stats */
              sum( (1-coalesce(s.stanullfrac, 0)) * coalesce(s.stawidth, 1024)) AS nulldatawidth,
              max( CASE WHEN a.atttypid = 'pg_catalog.name'::regtype THEN 1 ELSE 0 END ) > 0 AS is_na
          FROM (
              SELECT idxname, reltuples, relpages, tbloid, idxoid, fillfactor,
                  CASE WHEN indkey[i]=0 THEN idxoid ELSE tbloid END AS att_rel,
                  CASE WHEN indkey[i]=0 THEN i ELSE indkey[i] END AS att_pos
              FROM (
                  SELECT idxname, reltuples, relpages, tbloid, idxoid, fillfactor, indkey, generate_series(1,indnatts) AS i
                  FROM (
                      SELECT ci.relname AS idxname, ci.reltuples, ci.relpages, i.indrelid AS tbloid,
                          i.indexrelid AS idxoid,
                          coalesce(substring(
                              array_to_string(ci.reloptions, ' ')
                              from 'fillfactor=([0-9]+)')::smallint, 90) AS fillfactor,
                          i.indnatts,
                          string_to_array(textin(int2vectorout(i.indkey)),' ')::int[] AS indkey
                      FROM pg_index i
                      JOIN pg_class ci ON ci.oid=i.indexrelid
                      WHERE ci.relam=(SELECT oid FROM pg_am WHERE amname = 'btree')
                        AND ci.relpages > 0
                  ) AS idx_data
              ) AS idx_data_cross
          ) i
          JOIN pg_attribute a ON a.attrelid = i.att_rel
                             AND a.attnum = i.att_pos
          JOIN pg_statistic s ON s.starelid = i.att_rel
                             AND s.staattnum = i.att_pos
          JOIN pg_class ct ON ct.oid = i.tbloid
          JOIN pg_namespace n ON ct.relnamespace = n.oid
          GROUP BY 1,2,3,4,5,6,7,8,9,10
      ) AS rows_data_stats
  ) AS rows_hdr_pdg_stats
) AS relation_stats
ORDER BY nspname, tblname, idxname
"""  # noqa


SCHEMAS_SQL = """
SELECT n.nspname AS "name",
       COALESCE(schema_size, 0) AS total_bytes,
       pg_size_pretty(schema_size) AS total_size,
       COALESCE(n_tables, 0) AS n_tables,
       COALESCE(tables_bytes, 0) AS tables_bytes,
       pg_size_pretty(tables_bytes) AS tables_size,
       COALESCE(n_indexes, 0) AS n_indexes,
       COALESCE(indexes_bytes, 0) AS indexes_bytes,
       pg_size_pretty(indexes_bytes) AS indexes_size,
       tbloat.bloat_size AS tables_bloat_bytes,
       pg_size_pretty(tbloat.bloat_size::bigint) AS tables_bloat_size,
       ibloat.bloat_size AS indexes_bloat_bytes,
       pg_size_pretty(ibloat.bloat_size::bigint) AS indexes_bloat_size,
       COALESCE(toast.toast_bytes, 0) AS toast_bytes,
       pg_size_pretty(toast.toast_bytes) AS toast_size
FROM pg_catalog.pg_namespace n
-- schema size + tables for the schema (count, size)
-- See https://wiki.postgresql.org/wiki/Schema_Size
LEFT JOIN (
  SELECT schemaname,
         SUM(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename)))::BIGINT AS schema_size,
         count(*) as n_tables,
         SUM(pg_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename)))::BIGINT AS tables_bytes
  FROM pg_tables
  GROUP BY schemaname
) AS a
ON a.schemaname = n.nspname
-- toast size
LEFT JOIN (
  SELECT nspname,
         SUM(pg_total_relation_size(reltoastrelid)) AS toast_bytes
  FROM pg_class c
  LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
  GROUP BY nspname
) AS toast
ON toast.nspname = n.nspname
-- indexes for the schema (count, size)
LEFT JOIN (
  SELECT count(*) as n_indexes,
         schemaname,
         SUM(pg_relation_size(quote_ident(schemaname) || '.' || quote_ident(indexname)))::BIGINT AS indexes_bytes
  FROM pg_catalog.pg_indexes
  GROUP BY schemaname
) AS indexes
ON indexes.schemaname = n.nspname
LEFT JOIN (
  SELECT SUM(bloat_size) AS bloat_size,
         schemaname
  FROM (
    %s
  ) AS a
  GROUP BY schemaname
) AS tbloat
ON tbloat.schemaname = n.nspname
LEFT JOIN (
  SELECT SUM(bloat_size) AS bloat_size,
         schemaname
  FROM (
    %s
  ) AS a
  GROUP BY schemaname
) AS ibloat
ON ibloat.schemaname = n.nspname
WHERE n.nspname !~ '^pg_temp'
AND n.nspname !~ '^pg_toast'
""" % (TABLE_BLOAT_SQL, INDEX_BTREE_BLOAT_SQL)  # noqa


INDEXES_SQL = """
SELECT i.tablename AS tablename,
       i.indexname AS name,
       tablespace,
       x.indnatts AS number_of_columns,
       idx_scan AS scans,
       idx_tup_read,
       idx_tup_fetch,
       indexrelname,
       indisunique,
       i.indexdef AS def,
       total_bytes,
       pg_size_pretty(total_bytes) AS total_size,
       am.amname AS type,
       ibloat.bloat_size AS bloat_bytes,
       pg_size_pretty(ibloat.bloat_size::bigint) AS bloat_size
FROM pg_index x
JOIN (
    select oid, relname, relam, pg_total_relation_size(c.oid) AS total_bytes
    FROM pg_class c
) AS c
ON c.oid = x.indexrelid
JOIN pg_catalog.pg_indexes i
ON c.relname = i.indexname
JOIN pg_stat_all_indexes psai
ON x.indexrelid = psai.indexrelid
JOIN pg_am am
ON am.oid = c.relam
JOIN (
    WITH qq AS (
    """ + INDEX_BTREE_BLOAT_SQL + """
    ) SELECT * FROM qq
) AS ibloat
ON ibloat.schemaname = i.schemaname AND ibloat.tblname = i.tablename AND ibloat.idxname = i.indexname
WHERE i.schemaname = '{schema}'
{table_filter}
ORDER BY 1,2
"""  # noqa


def get_postgres(app_config, database):
    '''
    Same as `app.postgres` but with specific database not the default one.
    '''
    config = dict(**app_config.postgresql)
    config.update(dbname=database)
    return Postgres(**config)


def get_instance(conn):
    return conn.query("""\
    SELECT SUM(pg_database_size(datname)) AS total_bytes,
        pg_size_pretty(SUM(pg_database_size(datname))) AS total_size
    FROM pg_database
    WHERE NOT datistemplate;
    """)


def get_databases(conn):
    return list(conn.query("""\
    SELECT datname,
        pg_database_size(datname) AS total_bytes,
        pg_size_pretty(pg_database_size(datname)) AS total_size
    FROM pg_database
    WHERE NOT datistemplate;
    """))


def get_database_size(conn):
    return conn.queryone("""\
    SELECT pg_size_pretty(pg_database_size(current_database())) AS total_size,
        pg_database_size(current_database()) AS total_bytes
    """)


def get_database(conn):
    return conn.queryone("""
    SELECT SUM(n_tables) AS n_tables,
        SUM(tables_bytes) as tables_bytes,
        pg_size_pretty(SUM(tables_bytes)) AS tables_size,
        SUM(n_indexes) AS n_indexes,
        SUM(indexes_bytes) AS indexes_bytes,
        pg_size_pretty(SUM(indexes_bytes)) AS indexes_size,
        SUM(tables_bloat_bytes) AS tables_bloat_bytes,
        pg_size_pretty(SUM(tables_bloat_bytes)::bigint) AS tables_bloat_size,
        SUM(indexes_bloat_bytes) AS indexes_bloat_bytes,
        pg_size_pretty(SUM(indexes_bloat_bytes)::bigint) AS indexes_bloat_size,
        SUM(toast_bytes) AS toast_bytes,
        pg_size_pretty(SUM(toast_bytes)::bigint) AS toast_size
    FROM (%s) a""" % SCHEMAS_SQL)


def get_schemas(conn):
    return list(conn.query(SCHEMAS_SQL))


def get_schema(conn, schema):
    rows = conn.query("""\
    SELECT pg_size_pretty(bytes) AS size,  COALESCE(bytes, 0) as total_bytes
    FROM (
        SELECT schemaname, SUM(pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename)))::BIGINT AS bytes
        FROM pg_tables
        GROUP BY schemaname
    ) a
    WHERE schemaname = '{schema}'
    """.format(schema=schema)  # noqa
    )
    try:
        return next(rows)
    except StopIteration:
        return {}


def get_tables(conn, schema):
    # taken from https://wiki.postgresql.org/wiki/Disk_Usage
    query = """
SELECT table_name AS name,
       total_bytes,
       index_bytes,
       toast_bytes,
       table_bytes,
       COALESCE(n_indexes, 0) AS n_indexes,
       pg_size_pretty(total_bytes) AS total_size,
       pg_size_pretty(index_bytes) AS index_size,
       pg_size_pretty(toast_bytes) AS toast_size,
       pg_size_pretty(table_bytes) AS table_size,
       tbloat.bloat_size AS bloat_bytes,
       pg_size_pretty(tbloat.bloat_size::bigint) AS bloat_size,
       ibloat.bloat_size AS index_bloat_bytes,
       pg_size_pretty(ibloat.bloat_size::bigint) AS index_bloat_size,
       row_estimate
FROM (
  SELECT *, total_bytes - index_bytes - toast_bytes AS table_bytes
  FROM (
    SELECT c.oid,nspname AS table_schema,
           relname AS TABLE_NAME,
           c.reltuples AS row_estimate,
           pg_total_relation_size(c.oid) AS total_bytes,
           pg_indexes_size(c.oid) AS index_bytes,
           COALESCE(pg_total_relation_size(reltoastrelid), 0) AS toast_bytes
    FROM pg_class c
    LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE relkind = 'r'
  ) a
) a
LEFT JOIN (
  SELECT count(*) as n_indexes, tablename
  FROM pg_catalog.pg_indexes
  GROUP BY tablename
) AS indexes
ON indexes.tablename = table_name
JOIN (
  """ + TABLE_BLOAT_SQL + """
) AS tbloat
ON tbloat.schemaname = table_schema AND tbloat.tblname = table_name
LEFT JOIN (
  SELECT SUM(bloat_size) AS bloat_size,
         schemaname,
         tblname
  FROM (
    """ + INDEX_BTREE_BLOAT_SQL + """
  ) AS a
  GROUP BY schemaname, tblname
) AS ibloat
ON ibloat.schemaname = table_schema AND ibloat.tblname = table_name
WHERE table_schema = '{schema}';
    """ # noqa
    return {
        'tables': list(conn.query(query.format(schema=schema)))
    }


def get_schema_indexes(conn, schema):
    return {'indexes': list(conn.query(
        INDEXES_SQL.format(schema=schema, table_filter='')
    ))}


def get_table_indexes(conn, schema, table):
    return {'indexes': list(conn.query(
        INDEXES_SQL.format(
            schema=schema,
            table_filter="AND i.tablename = '%s'" % table
        )
    ))}


def get_table(conn, schema, table):
    query = """
SELECT table_name AS name,
       total_bytes,
       index_bytes,
       toast_bytes,
       table_bytes,
       pg_size_pretty(total_bytes) AS total_size,
       pg_size_pretty(index_bytes) AS index_size,
       pg_size_pretty(toast_bytes) AS toast_size,
       pg_size_pretty(table_bytes) AS table_size,
       pg_stat_all_tables.*,
       tbloat.bloat_size AS bloat_bytes,
       pg_size_pretty(tbloat.bloat_size::bigint) AS bloat_size,
       ibloat.bloat_size AS index_bloat_bytes,
       pg_size_pretty(ibloat.bloat_size::bigint) AS index_bloat_size,
       row_estimate,
       fillfactor
FROM (
  SELECT *, total_bytes - index_bytes - COALESCE(toast_bytes,0) AS table_bytes
  FROM (
    SELECT c.oid,nspname AS table_schema,
           relname AS TABLE_NAME,
           c.reltuples AS row_estimate,
           pg_total_relation_size(c.oid) AS total_bytes,
           pg_indexes_size(c.oid) AS index_bytes,
           pg_total_relation_size(reltoastrelid) AS toast_bytes
    FROM pg_class c
    LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE relkind = 'r'
  ) a
) a
JOIN (
  """ + TABLE_BLOAT_SQL + """
) AS tbloat
ON tbloat.schemaname = table_schema AND tbloat.tblname = table_name
LEFT JOIN (
  SELECT SUM(bloat_size) AS bloat_size,
         schemaname,
         tblname
  FROM (
    """ + INDEX_BTREE_BLOAT_SQL + """
  ) AS a
  GROUP BY schemaname, tblname
) AS ibloat
ON ibloat.schemaname = table_schema AND ibloat.tblname = table_name
JOIN pg_stat_all_tables
ON relname = table_name
WHERE table_schema = '{schema}'
AND table_name = '{table}';
    """
    return dict(conn.queryone(query.format(schema=schema, table=table)))


def check_table_exists(conn, schema, table):
    # Check that the specified table exists in schema
    rows = conn.query(
        "SELECT 1 FROM pg_tables WHERE tablename = '{table}' AND "
        "schemaname = '{schema}'".format(table=table, schema=schema)
    )
    if not list(rows):
        raise UserError("Table %s.%s not found" % (schema, table))


def check_index_exists(conn, schema, index):
    # Check that the specified table exists in schema
    rows = conn.query(
        "SELECT 1 FROM pg_indexes WHERE indexname = '{index}' AND "
        "schemaname = '{schema}'".format(index=index, schema=schema)
    )
    if not list(rows):
        raise UserError("Index %s.%s not found" % (schema, index))


def schedule_operation(operation_type, conn, database,
                       datetimeutc, app, table=None, index=None,
                       schema=None, **kwargs):
    # Schedule a maintenance operation (vacuum or analyze) statement through
    # background worker

    if table:
        check_table_exists(conn, schema, table)
    if index:
        check_index_exists(conn, schema, index)

    # Schedule a new task to background worker

    # We need to build a uniq id for this task to avoid scheduling twice the
    # same statement.
    m = hashlib.md5()
    m.update("{database}:{schema}:{table}{index}:{datetime}:{operation_type}"
             .format(database=database,
                     schema=schema or '',
                     table=table or '',
                     index=index or '',
                     datetime=datetimeutc,
                     operation_type=operation_type).encode('utf-8'))
    # Task scheduling
    try:
        # Convert string datetime to datetime object
        dt = datetime.strptime(datetimeutc, '%Y-%m-%dT%H:%M:%SZ')

        options = {
            'dbname': database,
        }
        if schema:
            options['schema'] = schema
        if table:
            options['table'] = table
        if index:
            options['index'] = index
        if 'mode' in kwargs:
            options['mode'] = kwargs['mode']

        res = taskmanager.schedule_task(
            operation_type + '_worker',
            id=m.hexdigest()[:8],
            options=options,
            # We add one microsecond here to be compliant with scheduler
            # datetime format expected during task recovery
            start=(dt + timedelta(microseconds=1)),
            listener_addr=str(os.path.join(app.config.temboard.home,
                                           '.tm.socket')),
            expire=0,
        )
    except Exception as e:
        logger.exception(str(e))
        raise HTTPError(500, "Unable to schedule %s" % operation_type)

    if res.type == taskmanager.MSG_TYPE_ERROR:
        logger.error(res.content)
        raise HTTPError(500, "Unable to schedule %s" % operation_type)

    return res.content


def schedule_vacuum(conn, database, mode, datetimeutc, app,
                    schema=None, table=None):
    return schedule_operation('vacuum', conn, database, datetimeutc, app,
                              mode=mode, schema=schema, table=table)


def vacuum(conn, dbname, mode, schema=None, table=None):
    # Run vacuum statement

    if table:
        check_table_exists(conn, schema, table)

    # Build the SQL query
    q = "VACUUM"
    q += " (%s) " % mode.upper() if mode else ""

    if schema and table:
        q += " {schema}.{table}".format(schema=schema, table=table)

    try:
        # Try to execute the statement
        logger.info("Running SQL on DB %s: %s" % (dbname, q))
        conn.execute(q)
        logger.info("VACCUM done.")
    except error as e:
        logger.exception(str(e))
        logger.error("Unable to execute SQL: %s" % q)
        message = "Unable to run vacuum %s" % mode
        if schema and table:
            message += " on %s.%s" % (schema, table,)

        raise UserError(message)


def task_status_label(status):
    labels = ['todo', 'scheduled', 'queued', 'doing', 'done', 'failed',
              'canceled', 'aborted', 'abort']
    p = status.bit_length() - 1
    try:
        return labels[p]
    except IndexError:
        return 'unknown'


def list_scheduled_operation(app, operation_type, **kwargs):
    # Get list of scheduled vacuum operations
    ret = []
    try:
        # Ask it to the task manager
        tasks = taskmanager.TaskManager.send_message(
            str(os.path.join(app.config.temboard.home, '.tm.socket')),
            taskmanager.Message(taskmanager.MSG_TYPE_TASK_LIST, ''),
            authkey=None,
        )
    except Exception as e:
        logger.exception(str(e))
        raise HTTPError(500, "Unable to get scheduled vacuum list")

    for task in tasks:

        # We only want tasks for the operation type ('vacuum', 'analyze',
        # 'reindex')
        if task.worker_name != operation_type + '_worker':
            continue

        options = task.options
        # Filter by db/schema/table if provided
        if (all(k in kwargs for k in ['dbname', 'schema']) and
            (kwargs.get('dbname') != options.get('dbname') or
             kwargs.get('schema') != options.get('schema'))):
            continue

        if ('table' in kwargs and kwargs.get('table') != options.get('table')):
            continue
        if ('index' in kwargs and kwargs.get('index') != options.get('index')):
            continue

        ret.append(dict(
            id=task.id,
            dbname=options.get('dbname'),
            schema=options.get('schema'),
            table=options.get('table'),
            index=options.get('index'),
            mode=options.get('mode'),
            datetime=task.start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
            status=task_status_label(task.status)
        ))
    return ret


def list_scheduled_vacuum(app, **kwargs):
    return list_scheduled_operation(app, 'vacuum', **kwargs)


def schedule_analyze(conn, database, datetimeutc, app,
                     schema=None, table=None):
    return schedule_operation('analyze', conn, database, datetimeutc, app,
                              schema=schema, table=table)


def analyze(conn, dbname, schema=None, table=None):
    # Run analyze statement
    if table:
        check_table_exists(conn, schema, table)

    # Build the SQL query
    q = "ANALYZE"
    if schema and table:
        q += " {schema}.{table}".format(schema=schema, table=table)

    try:
        # Try to execute the statement
        logger.info("Running SQL on DB %s: %s" % (dbname, q))
        conn.execute(q)
        logger.info("ANALYZE done.")
    except error as e:
        logger.exception(str(e))
        logger.error("Unable to execute SQL: %s" % q)
        message = "Unable to run analyze"
        if schema and table:
            message += " on %s.%s" % (schema, table,)

        raise UserError(message)


def list_scheduled_analyze(app, **kwargs):
    return list_scheduled_operation(app, 'analyze', **kwargs)


def schedule_reindex(conn, database, datetimeutc, app,
                     schema=None, table=None, index=None):
    return schedule_operation('reindex', conn, database, datetimeutc, app,
                              schema=schema, table=table, index=index)


def reindex(conn, dbname, schema, table, index):
    if index:
        check_index_exists(conn, schema, index)
    if table:
        check_table_exists(conn, schema, table)

    # Build the SQL query
    q = "REINDEX"
    if table:
        element = '{schema}.{table}'.format(schema=schema, table=table)
        q += " TABLE {element}".format(element=element)
    elif index:
        element = '{schema}.{index}'.format(schema=schema, index=index)
        q += " INDEX {element}".format(element=element)
    else:
        element = '{dbname}'.format(dbname=dbname)
        q += " DATABASE {element}".format(element=element)

    try:
        # Try to execute the statement
        logger.info("Running SQL on DB %s: %s" % (dbname, q))
        conn.execute(q)
        logger.info("reindex done.")
    except error as e:
        logger.exception(str(e))
        logger.error("Unable to execute SQL: %s" % q)
        raise UserError("Unable to run reindex on %s" % (element))


def list_scheduled_reindex(app, **kwargs):
    return list_scheduled_operation(app, 'reindex', **kwargs)


def cancel_scheduled_operation(id, app):
    # Cancel one scheduled operation. If the operation is running, the task
    # is going to be aborted.

    # Check the id
    if id not in [t['id'] for t in
                  list_scheduled_vacuum(app) +
                  list_scheduled_analyze(app) +
                  list_scheduled_reindex(app)]:
        raise HTTPError(404, "Scheduled operation not found")

    try:
        # Ask it to the task manager
        taskmanager.TaskManager.send_message(
            str(os.path.join(app.config.temboard.home, '.tm.socket')),
            taskmanager.Message(
                taskmanager.MSG_TYPE_TASK_CANCEL,
                dict(task_id=id),
            ),
            authkey=None,
        )
    except Exception as e:
        logger.exception(str(e))
        raise HTTPError(500, "Unable to cancel operation")

    return dict(response="ok")
