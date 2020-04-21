CREATE SCHEMA monitoring;
SET search_path TO monitoring, public;


-- A host is something running an operating system, it can be physical
-- or virtual. The primary key being the hostname it must be fully
-- qualified.
CREATE TABLE hosts (
  host_id SERIAL PRIMARY KEY,
  hostname TEXT NOT NULL UNIQUE, -- fqdn
  os TEXT NOT NULL, -- kernel name
  os_version TEXT NOT NULL, -- kernel version
  os_flavour TEXT, -- distribution
  cpu_count INTEGER,
  cpu_arch TEXT,
  memory_size BIGINT,
  swap_size BIGINT,
  virtual BOOLEAN
);

-- Instances are defined as running postgres processed that listen to
-- a specific TCP port
CREATE TABLE instances (
  instance_id SERIAL PRIMARY KEY,
  host_id INTEGER NOT NULL REFERENCES hosts (host_id) ON DELETE RESTRICT,
  port INTEGER NOT NULL,
  local_name TEXT NOT NULL, -- name of the instance inside the agent configuration
  version TEXT NOT NULL, -- dotted minor version
  version_num INTEGER NOT NULL, -- for comparisons (e.g. 90401)
  data_directory TEXT NOT NULL,
  sysuser TEXT, -- system user
  standby BOOLEAN NOT NULL DEFAULT false,
  UNIQUE (host_id, port)
);

-- Composite types for each type of record we need to store
CREATE TYPE metric_sessions_record AS (
  datetime TIMESTAMPTZ,
  active INTEGER,
  waiting INTEGER,
  idle INTEGER,
  idle_in_xact INTEGER,
  idle_in_xact_aborted INTEGER,
  fastpath INTEGER,
  disabled INTEGER,
  no_priv INTEGER
);

CREATE TYPE metric_xacts_record AS (
  datetime TIMESTAMPTZ,
  measure_interval INTERVAL,
  n_commit BIGINT,
  n_rollback BIGINT
);

CREATE TYPE metric_locks_record AS (
  datetime TIMESTAMPTZ,
  access_share INTEGER,
  row_share INTEGER,
  row_exclusive INTEGER,
  share_update_exclusive INTEGER,
  share INTEGER,
  share_row_exclusive INTEGER,
  exclusive INTEGER,
  access_exclusive INTEGER,
  siread INTEGER,
  waiting_access_share INTEGER ,
  waiting_row_share INTEGER,
  waiting_row_exclusive INTEGER,
  waiting_share_update_exclusive INTEGER,
  waiting_share INTEGER,
  waiting_share_row_exclusive INTEGER,
  waiting_exclusive INTEGER,
  waiting_access_exclusive INTEGER
);

CREATE TYPE metric_blocks_record AS (
  datetime TIMESTAMPTZ,
  measure_interval INTERVAL,
  blks_read BIGINT,
  blks_hit BIGINT,
  hitmiss_ratio FLOAT
);

CREATE TYPE metric_bgwriter_record AS (
  datetime TIMESTAMPTZ,
  measure_interval INTERVAL,
  checkpoints_timed BIGINT,
  checkpoints_req BIGINT,
  checkpoint_write_time DOUBLE PRECISION,
  checkpoint_sync_time DOUBLE PRECISION,
  buffers_checkpoint BIGINT,
  buffers_clean BIGINT,
  maxwritten_clean BIGINT,
  buffers_backend BIGINT,
  buffers_backend_fsync BIGINT,
  buffers_alloc BIGINT,
  stats_reset TIMESTAMPTZ
);

CREATE TYPE metric_db_size_record AS (
  datetime TIMESTAMPTZ,
  size BIGINT
);

CREATE TYPE metric_tblspc_size_record AS (
  datetime TIMESTAMPTZ,
  size BIGINT
);

CREATE TYPE metric_filesystems_size_record AS (
  datetime TIMESTAMPTZ,
  used BIGINT,
  total BIGINT,
  device TEXT
);

CREATE TYPE metric_temp_files_size_tblspc_record AS (
  datetime TIMESTAMPTZ,
  size BIGINT
);

CREATE TYPE metric_wal_files_record AS (
  datetime TIMESTAMPTZ,
  measure_interval INTERVAL,
  written_size BIGINT,
  current_location TEXT,
  total INTEGER,
  archive_ready INTEGER,
  total_size BIGINT
);

CREATE TYPE metric_cpu_record AS (
  datetime TIMESTAMPTZ,
  measure_interval INTERVAL,
  time_user BIGINT,
  time_system BIGINT,
  time_idle BIGINT,
  time_iowait BIGINT,
  time_steal BIGINT
);

CREATE TYPE metric_process_record AS (
  datetime TIMESTAMPTZ,
  measure_interval INTERVAL,
  context_switches BIGINT,
  forks BIGINT,
  procs_running INTEGER,
  procs_blocked INTEGER,
  procs_total INTEGER
);

CREATE TYPE metric_memory_record AS (
  datetime TIMESTAMPTZ,
  mem_total BIGINT,
  mem_used BIGINT,
  mem_free BIGINT,
  mem_buffers BIGINT,
  mem_cached BIGINT,
  swap_total BIGINT,
  swap_used BIGINT
);

CREATE TYPE metric_loadavg_record AS (
  datetime TIMESTAMPTZ,
  load1 FLOAT,
  load5 FLOAT,
  load15 FLOAT
);

CREATE TYPE metric_vacuum_analyze_record AS (
  datetime TIMESTAMPTZ,
  measure_interval INTERVAL,
  n_vacuum INTEGER,
  n_analyze INTEGER,
  n_autovacuum INTEGER,
  n_autoanalyze INTEGER
);

CREATE TYPE metric_replication_lag_record AS (
  datetime TIMESTAMPTZ,
  lag BIGINT
);

CREATE TYPE metric_replication_connection_record AS (
  datetime TIMESTAMPTZ,
  connected SMALLINT
);

CREATE TYPE metric_temp_files_size_delta_record AS (
  datetime TIMESTAMPTZ,
  measure_interval INTERVAL,
  size BIGINT
);

CREATE TYPE metric_bloat_ratio_record AS (
  datetime TIMESTAMPTZ,
  ratio FLOAT
);


-- Creation of the aggregate function: min(pg_lsn)
CREATE OR REPLACE FUNCTION pg_lsn_smaller(in_pg_lsn1 pg_lsn, in_pg_lsn2 pg_lsn) RETURNS pg_lsn
LANGUAGE plpgsql
AS $$
DECLARE
BEGIN
  IF in_pg_lsn1 < in_pg_lsn2 THEN
    RETURN in_pg_lsn1;
  ELSE
    RETURN in_pg_lsn2;
  END IF;
END;

$$;

CREATE AGGREGATE min (pg_lsn) ( SFUNC = pg_lsn_smaller, STYPE = pg_lsn, SORTOP = <);

CREATE OR REPLACE FUNCTION metric_tables_config() RETURNS json
LANGUAGE plpgsql
AS $$

DECLARE
  v_query JSON;
  v_conf JSON;
  q_metric_sessions_agg TEXT;
  q_metric_xacts_agg TEXT;
  q_metric_locks_agg TEXT;
  q_metric_blocks_agg TEXT;
  q_metric_bgwriter_agg TEXT;
  q_metric_db_size_agg TEXT;
  q_metric_tblspc_size_agg TEXT;
  q_metric_filesystems_size_agg TEXT;
  q_metric_temp_files_size_delta_agg TEXT;
  q_metric_wal_files_agg TEXT;
  q_metric_cpu_agg TEXT;
  q_metric_process_agg TEXT;
  q_metric_memory_agg TEXT;
  q_metric_loadavg_agg TEXT;
  q_metric_vacuum_analyze_agg TEXT;
  q_metric_replication_lag_agg TEXT;
  q_metric_replication_connection_agg TEXT;
  q_metric_bloat_ratio_agg TEXT;
BEGIN
  --
  -- Query template list for the actions: 'history' and 'expand'
  -- 'history': Move data from metric_<type>_current to metric_<type>_history, grouping records into array of records.
  -- 'expand': Return data from both metric_<type>_current and metric_<type>_history tables, depending on the time interval.
  --
  SELECT '{
    "history": {
      "host_id":     "INSERT INTO #history_table# SELECT tstzrange(min(datetime), max(datetime)), host_id, array_agg(set_datetime_record(datetime, record)::#record_type#) AS records FROM #current_table# GROUP BY date_trunc(''day'', datetime),2 ORDER BY 1,2 ASC;",
      "instance_id": "INSERT INTO #history_table# SELECT tstzrange(min(datetime), max(datetime)), instance_id, array_agg(set_datetime_record(datetime, record)::#record_type#) AS records FROM #current_table# GROUP BY date_trunc(''day'', datetime),2 ORDER BY 1,2 ASC;",
      "dbname":      "INSERT INTO #history_table# SELECT tstzrange(min(datetime), max(datetime)), instance_id, dbname, array_agg(set_datetime_record(datetime, record)::#record_type#) AS records FROM #current_table# GROUP BY date_trunc(''day'', datetime),2,3 ORDER BY 1,2 ASC;",
      "spcname":     "INSERT INTO #history_table# SELECT tstzrange(min(datetime), max(datetime)), instance_id, spcname, array_agg(set_datetime_record(datetime, record)::#record_type#) AS records FROM #current_table# GROUP BY date_trunc(''day'', datetime),2,3 ORDER BY 1,2,3 ASC;",
      "mount_point": "INSERT INTO #history_table# SELECT tstzrange(min(datetime), max(datetime)), host_id, mount_point, array_agg(set_datetime_record(datetime, record)::#record_type#) AS records FROM #current_table# AS deleted_rows GROUP BY date_trunc(''day'', datetime),2,3 ORDER BY 1,2,3 ASC;",
      "cpu":         "INSERT INTO #history_table# SELECT tstzrange(min(datetime), max(datetime)), host_id, cpu, array_agg(set_datetime_record(datetime, record)::#record_type#) AS records FROM #current_table# AS deleted_rows GROUP BY date_trunc(''day'', datetime),2,3 ORDER BY 1,2,3 ASC;",
      "upstream":    "INSERT INTO #history_table# SELECT tstzrange(min(datetime), max(datetime)), instance_id, upstream, array_agg(set_datetime_record(datetime, record)::#record_type#) AS records FROM #current_table# AS deleted_rows GROUP BY date_trunc(''day'', datetime),2,3 ORDER BY 1,2,3 ASC;"
    },
    "expand": {
      "host_id": "WITH expand AS (SELECT datetime, host_id, record FROM #current_table# WHERE #where_current# UNION SELECT (hist_query.record).datetime, host_id, hist_query.record FROM (SELECT host_id, unnest(records)::#record_type# AS record FROM #history_table# WHERE #where_history#) AS hist_query) SELECT * FROM expand WHERE datetime <@ #tstzrange# ORDER BY datetime ASC",
      "instance_id": "WITH expand AS (SELECT datetime, instance_id, record FROM #current_table# WHERE #where_current# UNION SELECT (hist_query.record).datetime, instance_id, hist_query.record FROM (SELECT instance_id, unnest(records)::#record_type# AS record FROM #history_table# WHERE #where_history#) AS hist_query) SELECT * FROM expand WHERE datetime <@ #tstzrange# ORDER BY datetime ASC",
      "dbname": "WITH expand AS (SELECT datetime, instance_id, dbname, record FROM #current_table# WHERE #where_current# UNION SELECT (hist_query.record).datetime, instance_id, dbname, hist_query.record FROM (SELECT instance_id, dbname, unnest(records)::#record_type# AS record FROM #history_table# WHERE #where_history#) AS hist_query) SELECT * FROM expand WHERE datetime <@ #tstzrange# ORDER BY datetime ASC",
      "spcname":"WITH expand AS (SELECT datetime, instance_id, spcname, record FROM #current_table# WHERE #where_current# UNION SELECT (hist_query.record).datetime, instance_id, spcname, hist_query.record FROM (SELECT instance_id, spcname, unnest(records)::#record_type# AS record FROM #history_table# WHERE #where_history#) AS hist_query) SELECT * FROM expand WHERE datetime <@ #tstzrange# ORDER BY datetime ASC",
      "mount_point": "WITH expand AS (SELECT datetime, host_id, mount_point, record FROM #current_table# WHERE #where_current# UNION SELECT (hist_query.record).datetime, host_id, mount_point, hist_query.record FROM (SELECT host_id, mount_point, unnest(records)::#record_type# AS record FROM #history_table# WHERE #where_history#) AS hist_query) SELECT * FROM expand WHERE datetime <@ #tstzrange# ORDER BY datetime ASC",
      "cpu": "WITH expand AS (SELECT datetime, host_id, cpu, record FROM #current_table# WHERE #where_current# UNION SELECT (hist_query.record).datetime, host_id, cpu, hist_query.record FROM (SELECT host_id, cpu, unnest(records)::#record_type# AS record FROM #history_table# WHERE #where_history#) AS hist_query) SELECT * FROM expand WHERE datetime <@ #tstzrange# ORDER BY datetime ASC",
      "upstream": "WITH expand AS (SELECT datetime, instance_id, upstream, record FROM #current_table# WHERE #where_current# UNION SELECT (hist_query.record).datetime, instance_id, upstream, hist_query.record FROM (SELECT instance_id, upstream, unnest(records)::#record_type# AS record FROM #history_table# WHERE #where_history#) AS hist_query) SELECT * FROM expand WHERE datetime <@ #tstzrange# ORDER BY datetime ASC"
    }
  }'::JSON INTO v_query;

  --
  -- Global configuration.
  --
  -- For each type of metric we have to deal with, there is the following object defining some properties:
  -- // Unique key used to find the configuration based on the metric name.
  -- "<metric_name>": {
  --   // Tables name prefix, for ease stuff it should be the same as <metric_name>
  --   "name": "<metric_tbl_name>",
  --   // Record composite type
  --   "record_type": "<metric_record_type>",
  --   // List of extra columns.
  --   "columns": [
  --     {
  --       // Column name
  --       "name": "<column_name>",
  --       // Column data type
  --       "data_type": "<column_data_type>"
  --     },
  --     [...]
  --   ],
  --   // Query template use to history data.
  --   "history": "<query_tpl_history>",
  --   // Query template use to fetch data from both _current & _history tables.
  --   "expand": "<query_tpl_expand>",
  --   // Query template use to aggregate data.
  --   "aggregate": "<query_tpl_aggregate>"
  -- }

  q_metric_sessions_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    instance_id,
    dbname,
    ROW(
      NULL,
      AVG((r).active),
      AVG((r).waiting),
      AVG((r).idle),
      AVG((r).idle_in_xact),
      AVG((r).idle_in_xact_aborted),
      AVG((r).fastpath),
      AVG((r).disabled),
      AVG((r).no_priv)
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      instance_id integer,
      dbname text,
      r #record_type#
   )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2,3
  ORDER BY 1,2,3
ON CONFLICT (datetime, instance_id, dbname)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_xacts_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    instance_id,
    dbname,
    ROW(
      NULL,
      SUM((r).measure_interval),
      SUM((r).n_commit),
      SUM((r).n_rollback)
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
  AS (
    datetime timestamp with time zone,
    instance_id integer,
    dbname text,
    r #record_type#
  )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2,3
  ORDER BY 1,2,3
ON CONFLICT (datetime, instance_id, dbname)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_locks_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    instance_id,
    dbname,
    ROW(
      NULL,
      AVG((r).access_share),
      AVG((r).row_share),
      AVG((r).row_exclusive),
      AVG((r).share_update_exclusive),
      AVG((r).share),
      AVG((r).share_row_exclusive),
      AVG((r).exclusive),
      AVG((r).access_exclusive),
      AVG((r).siread),
      AVG((r).waiting_access_share),
      AVG((r).waiting_row_share),
      AVG((r).waiting_row_exclusive),
      AVG((r).waiting_share_update_exclusive),
      AVG((r).waiting_share),
      AVG((r).waiting_share_row_exclusive),
      AVG((r).waiting_exclusive),
      AVG((r).waiting_access_exclusive)
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      instance_id integer,
      dbname text,
      r #record_type#
    )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2,3
  ORDER BY 1,2,3
ON CONFLICT (datetime, instance_id, dbname)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_blocks_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    instance_id,
    dbname,
    ROW(
      NULL,
      SUM((r).measure_interval),
      SUM((r).blks_read),
      SUM((r).blks_hit),
      AVG((r).hitmiss_ratio)
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      instance_id integer,
      dbname text,
      r #record_type#
    )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2,3
  ORDER BY 1,2,3
ON CONFLICT (datetime, instance_id, dbname)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_bgwriter_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    instance_id,
    ROW(
      NULL,
      SUM((r).measure_interval),
      SUM((r).checkpoints_timed),
      SUM((r).checkpoints_req),
      SUM((r).checkpoint_write_time),
      SUM((r).checkpoint_sync_time),
      SUM((r).buffers_checkpoint),
      SUM((r).buffers_clean),
      SUM((r).maxwritten_clean),
      SUM((r).buffers_backend),
      SUM((r).buffers_backend_fsync),
      SUM((r).buffers_alloc),
      NULL
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      instance_id integer,
      r #record_type#
    )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2
  ORDER BY 1,2
ON CONFLICT (datetime, instance_id)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_db_size_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    instance_id,
    dbname,
    ROW(
      NULL,
      AVG((r).size)
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      instance_id integer,
      dbname text,
      r #record_type#
    )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2,3
  ORDER BY 1,2,3
ON CONFLICT (datetime, instance_id, dbname)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_tblspc_size_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    instance_id,
    spcname,
    ROW(
      NULL,
      AVG((r).size)
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      instance_id integer,
      spcname text,
      r #record_type#
    )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2,3
  ORDER BY 1,2,3
ON CONFLICT (datetime, instance_id, spcname)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_filesystems_size_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    host_id,
    mount_point,
    ROW(
      NULL,
      AVG((r).used),
      AVG((r).total),
      NULL
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      host_id integer,
      mount_point text,
      r #record_type#
    )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2,3
  ORDER BY 1,2,3
ON CONFLICT (datetime, host_id, mount_point)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_temp_files_size_delta_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    instance_id,
    dbname,
    ROW(
      NULL,
      SUM((r).measure_interval),
      SUM((r).size)
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      instance_id integer,
      dbname text,
      r #record_type#
    )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2,3
  ORDER BY 1,2,3
ON CONFLICT (datetime, instance_id, dbname)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_wal_files_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    instance_id,
    ROW(
      NULL,
      SUM((r).measure_interval),
      MAX((r).written_size),
      MIN((r).current_location::pg_lsn)::TEXT,
      MAX((r).total),
      MAX((r).archive_ready),
      MAX((r).total_size)
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      instance_id integer,
      r #record_type#
    )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2
  ORDER BY 1,2
ON CONFLICT (datetime, instance_id)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_cpu_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    host_id,
    cpu,
    ROW(
      NULL,
      SUM((r).measure_interval),
      SUM((r).time_user),
      SUM((r).time_system),
      SUM((r).time_idle),
      SUM((r).time_iowait),
      SUM((r).time_steal)
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      host_id integer,
      cpu text,
      r #record_type#
    )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2,3
  ORDER BY 1,2,3
ON CONFLICT (datetime, host_id, cpu)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_process_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    host_id,
    ROW(
      NULL,
      SUM((r).measure_interval),
      SUM((r).context_switches),
      SUM((r).forks),
      AVG((r).procs_running),
      AVG((r).procs_blocked),
      AVG((r).procs_total)
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      host_id integer,
      r #record_type#
    )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2
  ORDER BY 1,2
ON CONFLICT (datetime, host_id)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_memory_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    host_id,
    ROW(
      NULL,
      AVG((r).mem_total),
      AVG((r).mem_used),
      AVG((r).mem_free),
      AVG((r).mem_buffers),
      AVG((r).mem_cached),
      AVG((r).swap_total),
      AVG((r).swap_used)
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      host_id integer,
      r #record_type#
    )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2
  ORDER BY 1,2
ON CONFLICT (datetime, host_id)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_loadavg_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    host_id,
    ROW(
      NULL,
      ROUND(AVG((r).load1)::NUMERIC, 2),
      ROUND(AVG((r).load5)::NUMERIC, 2),
      ROUND(AVG((r).load15)::NUMERIC, 2)
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      host_id integer,
      r #record_type#
    )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2
  ORDER BY 1,2
ON CONFLICT (datetime, host_id)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_vacuum_analyze_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    instance_id,
    dbname,
    ROW(
      NULL,
      SUM((r).measure_interval),
      SUM((r).n_vacuum),
      SUM((r).n_analyze),
      SUM((r).n_autovacuum),
      SUM((r).n_autoanalyze)
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      instance_id integer,
      dbname text,
      r #record_type#
    )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2,3
  ORDER BY 1,2,3
ON CONFLICT (datetime, instance_id, dbname)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_replication_lag_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    instance_id,
    ROW(
      NULL,
      AVG((r).lag)
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      instance_id integer,
      r #record_type#
    )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2
  ORDER BY 1,2
ON CONFLICT (datetime, instance_id)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_replication_connection_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    instance_id,
    upstream,
    ROW(
      NULL,
      AVG((r).connected)::INT
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      instance_id integer,
      upstream text,
      r #record_type#
   )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2,3
  ORDER BY 1,2,3
ON CONFLICT (datetime, instance_id, upstream)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');

  q_metric_bloat_ratio_agg := replace(to_json($_$
INSERT INTO #agg_table#
  SELECT
    truncate_time(datetime, '#interval#') AS datetime,
    instance_id,
    dbname,
    ROW(
      NULL,
      AVG((r).ratio)
    )::#record_type#,
    COUNT(*) AS w
  FROM
    expand_data_limit('#name#', (SELECT tstzrange(MAX(datetime), NOW()) FROM #agg_table#), 100000)
    AS (
      datetime timestamp with time zone,
      instance_id integer,
      dbname text,
      r #record_type#
    )
  WHERE
    truncate_time(datetime, '#interval#') < truncate_time(NOW(), '#interval#')
  GROUP BY 1,2,3
  ORDER BY 1,2,3
ON CONFLICT (datetime, instance_id, dbname)
DO UPDATE SET w = EXCLUDED.w, record = EXCLUDED.record
WHERE #agg_table#.w < EXCLUDED.w
$_$::TEXT)::TEXT, '\n', ' ');


  SELECT ('{
  "metric_sessions": {
    "name": "metric_sessions",
    "record_type": "metric_sessions_record",
    "columns":
    [
      {"name": "instance_id", "data_type": "INTEGER NOT NULL REFERENCES instances (instance_id) ON DELETE CASCADE"},
      {"name": "dbname", "data_type": "TEXT NOT NULL"}
    ],
    "history": "'||(v_query->'history'->>'dbname')||'",
    "expand": "'||(v_query->'expand'->>'dbname')||'",
    "aggregate": '||q_metric_sessions_agg||'
  },
  "metric_xacts": {
    "name": "metric_xacts",
    "record_type": "metric_xacts_record",
    "columns":
    [
      {"name": "instance_id", "data_type": "INTEGER NOT NULL REFERENCES instances (instance_id) ON DELETE CASCADE"},
      {"name": "dbname", "data_type": "TEXT NOT NULL"}
    ],
    "history": "'||(v_query->'history'->>'dbname')||'",
    "expand": "'||(v_query->'expand'->>'dbname')||'",
    "aggregate": '||q_metric_xacts_agg||'
  },
  "metric_locks": {
    "name": "metric_locks",
    "record_type": "metric_locks_record",
    "columns":
    [
      {"name": "instance_id", "data_type": "INTEGER NOT NULL REFERENCES instances (instance_id) ON DELETE CASCADE"},
      {"name": "dbname", "data_type": "TEXT NOT NULL"}
    ],
    "history": "'||(v_query->'history'->>'dbname')||'",
    "expand": "'||(v_query->'expand'->>'dbname')||'",
    "aggregate": '||q_metric_locks_agg||'
  },
  "metric_blocks": {
    "name": "metric_blocks",
    "record_type": "metric_blocks_record",
    "columns":
    [
      {"name": "instance_id", "data_type": "INTEGER NOT NULL REFERENCES instances (instance_id) ON DELETE CASCADE"},
      {"name": "dbname", "data_type": "TEXT NOT NULL"}
    ],
    "history": "'||(v_query->'history'->>'dbname')||'",
    "expand": "'||(v_query->'expand'->>'dbname')||'",
    "aggregate": '||q_metric_blocks_agg||'
  },
  "metric_bgwriter": {
    "name": "metric_bgwriter",
    "record_type": "metric_bgwriter_record",
    "columns":
    [
      {"name": "instance_id", "data_type": "INTEGER NOT NULL REFERENCES instances (instance_id) ON DELETE CASCADE"}
    ],
    "history": "'||(v_query->'history'->>'instance_id')||'",
    "expand": "'||(v_query->'expand'->>'instance_id')||'",
    "aggregate": '||q_metric_bgwriter_agg||'
  },
  "metric_db_size": {
    "name": "metric_db_size",
    "record_type": "metric_db_size_record",
    "columns":
    [
      {"name": "instance_id", "data_type": "INTEGER NOT NULL REFERENCES instances (instance_id) ON DELETE CASCADE"},
      {"name": "dbname", "data_type": "TEXT NOT NULL"}
    ],
    "history": "'||(v_query->'history'->>'dbname')||'",
    "expand": "'||(v_query->'expand'->>'dbname')||'",
    "aggregate": '||q_metric_db_size_agg||'
  },
  "metric_tblspc_size": {
    "name": "metric_tblspc_size",
    "record_type": "metric_tblspc_size_record",
    "columns":
    [
      {"name": "instance_id", "data_type": "INTEGER NOT NULL REFERENCES instances (instance_id) ON DELETE CASCADE"},
      {"name": "spcname", "data_type": "TEXT NOT NULL"}
    ],
    "history": "'||(v_query->'history'->>'spcname')||'",
    "expand": "'||(v_query->'expand'->>'spcname')||'",
    "aggregate": '||q_metric_tblspc_size_agg||'
  },
  "metric_filesystems_size": {
    "name": "metric_filesystems_size",
    "record_type": "metric_filesystems_size_record",
    "columns":
    [
      {"name": "host_id", "data_type": "INTEGER NOT NULL REFERENCES hosts (host_id) ON DELETE CASCADE"},
      {"name": "mount_point", "data_type": "TEXT NOT NULL"}
    ],
    "history": "'||(v_query->'history'->>'mount_point')||'",
    "expand": "'||(v_query->'expand'->>'mount_point')||'",
    "aggregate": '||q_metric_filesystems_size_agg||'
  },
  "metric_temp_files_size_delta": {
    "name": "metric_temp_files_size_delta",
    "record_type": "metric_temp_files_size_delta_record",
    "columns":
    [
      {"name": "instance_id", "data_type": "INTEGER NOT NULL REFERENCES instances (instance_id) ON DELETE CASCADE"},
      {"name": "dbname", "data_type": "TEXT NOT NULL"}
    ],
    "history": "'||(v_query->'history'->>'dbname')||'",
    "expand": "'||(v_query->'expand'->>'dbname')||'",
    "aggregate": '||q_metric_temp_files_size_delta_agg||'
  },
  "metric_wal_files": {
    "name": "metric_wal_files",
    "record_type": "metric_wal_files_record",
    "columns":
    [
      {"name": "instance_id", "data_type": "INTEGER NOT NULL REFERENCES instances (instance_id) ON DELETE CASCADE"}
    ],
    "history": "'||(v_query->'history'->>'instance_id')||'",
    "expand": "'||(v_query->'expand'->>'instance_id')||'",
    "aggregate": '||q_metric_wal_files_agg||'
  },
  "metric_cpu": {
    "name": "metric_cpu",
    "record_type": "metric_cpu_record",
    "columns":
    [
      {"name": "host_id", "data_type": "INTEGER NOT NULL REFERENCES hosts (host_id) ON DELETE CASCADE"},
      {"name": "cpu", "data_type": "TEXT NOT NULL"}
    ],
    "history": "'||(v_query->'history'->>'cpu')||'",
    "expand": "'||(v_query->'expand'->>'cpu')||'",
    "aggregate": '||q_metric_cpu_agg||'
  },
  "metric_process": {
    "name": "metric_process",
    "record_type": "metric_process_record",
    "columns":
    [
      {"name": "host_id", "data_type": "INTEGER NOT NULL REFERENCES hosts (host_id) ON DELETE CASCADE"}
    ],
    "history": "'||(v_query->'history'->>'host_id')||'",
    "expand": "'||(v_query->'expand'->>'host_id')||'",
    "aggregate": '||q_metric_process_agg||'
  },
  "metric_memory": {
    "name": "metric_memory",
    "record_type": "metric_memory_record",
    "columns":
    [
      {"name": "host_id", "data_type": "INTEGER NOT NULL REFERENCES hosts (host_id) ON DELETE CASCADE"}
    ],
    "history": "'||(v_query->'history'->>'host_id')||'",
    "expand": "'||(v_query->'expand'->>'host_id')||'",
    "aggregate": '||q_metric_memory_agg||'
  },
  "metric_loadavg": {
    "name": "metric_loadavg",
    "record_type": "metric_loadavg_record",
    "columns":
    [
      {"name": "host_id", "data_type": "INTEGER NOT NULL REFERENCES hosts (host_id) ON DELETE CASCADE"}
    ],
    "history": "'||(v_query->'history'->>'host_id')||'",
    "expand": "'||(v_query->'expand'->>'host_id')||'",
    "aggregate": '||q_metric_loadavg_agg||'
  },
  "metric_vacuum_analyze": {
    "name": "metric_vacuum_analyze",
    "record_type": "metric_vacuum_analyze_record",
    "columns":
    [
      {"name": "instance_id", "data_type": "INTEGER NOT NULL REFERENCES instances (instance_id) ON DELETE CASCADE"},
      {"name": "dbname", "data_type": "TEXT NOT NULL"}
    ],
    "history": "'||(v_query->'history'->>'dbname')||'",
    "expand": "'||(v_query->'expand'->>'dbname')||'",
    "aggregate": '||q_metric_vacuum_analyze_agg||'
  },
  "metric_replication_lag": {
    "name": "metric_replication_lag",
    "record_type": "metric_replication_lag_record",
    "columns":
    [
      {"name": "instance_id", "data_type": "INTEGER NOT NULL REFERENCES instances (instance_id) ON DELETE CASCADE"}
    ],
    "history": "'||(v_query->'history'->>'instance_id')||'",
    "expand": "'||(v_query->'expand'->>'instance_id')||'",
    "aggregate": '||q_metric_replication_lag_agg||'
  },
  "metric_replication_connection": {
    "name": "metric_replication_connection",
    "record_type": "metric_replication_connection_record",
    "columns":
    [
      {"name": "instance_id", "data_type": "INTEGER NOT NULL REFERENCES instances (instance_id) ON DELETE CASCADE"},
      {"name": "upstream", "data_type": "TEXT NOT NULL"}
    ],
    "history": "'||(v_query->'history'->>'upstream')||'",
    "expand": "'||(v_query->'expand'->>'upstream')||'",
    "aggregate": '||q_metric_replication_connection_agg||'
  },
  "metric_heap_bloat": {
    "name": "metric_heap_bloat",
    "record_type": "metric_bloat_ratio_record",
    "columns":
    [
      {"name": "instance_id", "data_type": "INTEGER NOT NULL REFERENCES instances (instance_id) ON DELETE CASCADE"},
      {"name": "dbname", "data_type": "TEXT NOT NULL"}
    ],
    "history": "'||(v_query->'history'->>'dbname')||'",
    "expand": "'||(v_query->'expand'->>'dbname')||'",
    "aggregate": '||q_metric_bloat_ratio_agg||'
  },
  "metric_btree_bloat": {
    "name": "metric_btree_bloat",
    "record_type": "metric_bloat_ratio_record",
    "columns":
    [
      {"name": "instance_id", "data_type": "INTEGER NOT NULL REFERENCES instances (instance_id) ON DELETE CASCADE"},
      {"name": "dbname", "data_type": "TEXT NOT NULL"}
    ],
    "history": "'||(v_query->'history'->>'dbname')||'",
    "expand": "'||(v_query->'expand'->>'dbname')||'",
    "aggregate": '||q_metric_bloat_ratio_agg||'
  }}')::JSON INTO v_conf;
  RETURN v_conf;

END;

$$;


CREATE OR REPLACE FUNCTION create_tables() RETURNS TABLE(tblname TEXT)
LANGUAGE plpgsql
AS $$
DECLARE
  t JSON;
  c JSON;
  v_agg_periods TEXT[] := array['30m', '6h'];
  v_create_tbl_cols_cur TEXT;
  v_create_idx_cols_cur TEXT;
  v_create_tbl_cols_hist TEXT;
  v_create_idx_cols_hist TEXT;
  v_tablename TEXT;
  v_like_tablename TEXT;
  v_create_tbl_stmt TEXT;
  v_create_idx_stmt TEXT;
  i_period TEXT;
BEGIN
  -- Tables creation if they do not exist
  FOR t IN SELECT metric_tables_config()->json_object_keys(metric_tables_config()) LOOP
    v_create_tbl_cols_cur := 'datetime TIMESTAMPTZ NOT NULL';
    v_create_idx_cols_cur := 'datetime';
    FOR c IN SELECT json_array_elements(t->'columns') LOOP
      v_create_tbl_cols_cur := v_create_tbl_cols_cur||', '||trim((c->'name')::TEXT, '"')||' '||trim((c->'data_type')::TEXT, '"');
      v_create_idx_cols_cur := v_create_idx_cols_cur||', '||trim((c->'name')::TEXT, '"');
    END LOOP;

  -- Creation of current table.
    v_tablename := trim((t->'name')::TEXT, '"')||'_current';
    PERFORM 1 FROM pg_tables WHERE tablename = v_tablename AND schemaname = current_schema();
    IF NOT FOUND THEN
      EXECUTE 'CREATE TABLE '||v_tablename||' ('||v_create_tbl_cols_cur||', record '||trim((t->'record_type')::TEXT, '"')||')';
      EXECUTE 'CREATE INDEX idx_'||v_tablename||' ON '||v_tablename||' ('||v_create_idx_cols_cur||')';
      RETURN QUERY SELECT v_tablename;
    END IF;

    -- Creation of history table.
    v_create_tbl_cols_hist := 'history_range TSTZRANGE NOT NULL';
    v_create_idx_cols_hist := 'history_range';
    FOR c IN SELECT json_array_elements(t->'columns') LOOP
      v_create_tbl_cols_hist := v_create_tbl_cols_hist||', '||trim((c->'name')::TEXT, '"')||' '||trim((c->'data_type')::TEXT, '"');
      v_create_idx_cols_hist := v_create_idx_cols_hist||', '||trim((c->'name')::TEXT, '"');
    END LOOP;

    v_tablename := trim((t->'name')::TEXT, '"')||'_history';
    PERFORM 1 FROM pg_tables WHERE tablename = v_tablename AND schemaname = current_schema();
    IF NOT FOUND THEN
      EXECUTE 'CREATE TABLE '||v_tablename||' ('||v_create_tbl_cols_hist||', records '||trim((t->'record_type')::TEXT, '"')||'[])';
      EXECUTE 'CREATE INDEX idx_'||v_tablename||' ON '||v_tablename||' ('||v_create_idx_cols_hist||')';
      RETURN QUERY SELECT v_tablename;
    END IF;

    -- Aggregate tables creation.
    FOREACH i_period IN ARRAY v_agg_periods LOOP
      v_tablename := trim((t->'name')::TEXT, '"')||'_'||i_period||'_current';
      v_like_tablename := trim((t->'name')::TEXT, '"')||'_current';
      PERFORM 1 FROM pg_tables WHERE tablename = v_tablename AND schemaname = current_schema();
      IF NOT FOUND THEN
        EXECUTE 'CREATE TABLE '||v_tablename||' (LIKE '||v_like_tablename||')';
        -- Weight: number of record aggregated
        EXECUTE 'ALTER TABLE '||v_tablename||' ADD COLUMN w INTEGER DEFAULT 1';
        EXECUTE 'ALTER TABLE '||v_tablename||' ADD UNIQUE ('||v_create_idx_cols_cur||')';
        RETURN QUERY SELECT v_tablename;
      END IF;
    END LOOP;
  END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION history_tables() RETURNS TABLE(tblname TEXT, nb_rows INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
  t JSON;
  v_table_current TEXT;
  v_table_history TEXT;
  v_query TEXT;
  i INTEGER;
BEGIN
  -- History data from each _current table
  FOR t IN SELECT metric_tables_config()->json_object_keys(metric_tables_config()) LOOP
    v_table_current := trim((t->'name')::TEXT, '"')||'_current';
    v_table_history := trim((t->'name')::TEXT, '"')||'_history';
    -- Lock _current table to prevent concurrent updates
    EXECUTE 'LOCK TABLE '||v_table_current||' IN SHARE MODE';
    v_query := replace(t->>'history', '#history_table#', v_table_history);
    v_query := replace(v_query, '#current_table#', v_table_current);
    v_query := replace(v_query, '#record_type#', trim((t->'record_type')::TEXT, '"'));
    -- Move data into _history table
    EXECUTE v_query;
    GET DIAGNOSTICS i = ROW_COUNT;
    -- Truncate _current table
    EXECUTE 'TRUNCATE '||v_table_current;
    -- Return each history table name and the number of rows inserted
    RETURN QUERY SELECT v_table_history, i;
  END LOOP;
END;
$$;


CREATE OR REPLACE FUNCTION build_expand_data_query(i_name TEXT, i_range TSTZRANGE) RETURNS TEXT
LANGUAGE plpgsql
AS $$

DECLARE
  t JSON;
  v_query TEXT;
  v_table_current TEXT;
  v_table_history TEXT;
BEGIN
  -- Build and execute 'expand' query
  SELECT metric_tables_config()->i_name INTO t;
  v_query := t->>'expand';
  v_table_current := trim((t->'name')::TEXT, '"')||'_current';
  v_table_history := trim((t->'name')::TEXT, '"')||'_history';
  v_query := replace(v_query, '#history_table#', v_table_history);
  v_query := replace(v_query, '#current_table#', v_table_current);
  v_query := replace(v_query, '#record_type#', trim((t->'record_type')::TEXT, '"'));
  v_query := replace(v_query, '#where_current#', 'datetime <@ '''||i_range::TEXT||'''::TSTZRANGE');
  v_query := replace(v_query, '#where_history#', 'history_range && '''||i_range::TEXT||'''::TSTZRANGE');
  v_query := replace(v_query, '#tstzrange#', ''''||i_range::TEXT||'''::TSTZRANGE');
  RETURN v_query;
END;

$$;


CREATE OR REPLACE FUNCTION expand_data(i_name TEXT, i_range TSTZRANGE) RETURNS SETOF RECORD
LANGUAGE plpgsql
AS $$

DECLARE
  v_query TEXT;
BEGIN
  -- Build and execute 'expand' query
  SELECT monitoring.build_expand_data_query(i_name, i_range) INTO v_query;
  RAISE NOTICE '%', v_query;
  RETURN QUERY EXECUTE v_query;
END;

$$;


CREATE OR REPLACE FUNCTION expand_data_limit(i_name TEXT, i_range TSTZRANGE, i_limit INTEGER) RETURNS SETOF RECORD
LANGUAGE plpgsql
AS $$

DECLARE
  v_query TEXT;
BEGIN
  -- Build and execute 'expand' query
  SELECT monitoring.build_expand_data_query(i_name, i_range) INTO v_query;
  v_query := v_query||' LIMIT '||i_limit::TEXT;
  RAISE NOTICE '%', v_query;
  RETURN QUERY EXECUTE v_query;
END;

$$;


CREATE OR REPLACE FUNCTION expand_data_by_host_id(i_name TEXT, i_range TSTZRANGE, host_id INTEGER) RETURNS SETOF RECORD
LANGUAGE plpgsql
AS $$

DECLARE
  t JSON;
  v_query TEXT;
  v_table_current TEXT;
  v_table_history TEXT;
BEGIN

  -- Build and execute 'expand' query and filter results by host_id.
  SELECT metric_tables_config()->i_name INTO t;
  v_query := t->>'expand';
  v_table_current := trim((t->'name')::TEXT, '"')||'_current';
  v_table_history := trim((t->'name')::TEXT, '"')||'_history';
  v_query := replace(v_query, '#history_table#', v_table_history);
  v_query := replace(v_query, '#current_table#', v_table_current);
  v_query := replace(v_query, '#record_type#', trim((t->'record_type')::TEXT, '"'));
  v_query := replace(v_query, '#where_current#', 'host_id = '||host_id||' AND datetime <@ '''||i_range::TEXT||'''::TSTZRANGE');
  v_query := replace(v_query, '#where_history#', 'host_id = '||host_id||' AND history_range && '''||i_range::TEXT||'''::TSTZRANGE');
  v_query := replace(v_query, '#tstzrange#', ''''||i_range::TEXT||'''::TSTZRANGE');
  RAISE NOTICE '%', v_query;
  RETURN QUERY EXECUTE v_query;
END;

$$;

CREATE OR REPLACE FUNCTION expand_data_by_instance_id(i_name TEXT, i_range TSTZRANGE, instance_id INTEGER) RETURNS SETOF RECORD
LANGUAGE plpgsql
AS $$

DECLARE
  t JSON;
  v_query TEXT;
  v_table_current TEXT;
  v_table_history TEXT;
BEGIN

  SELECT metric_tables_config()->i_name INTO t;
  v_query := t->>'expand';
  v_table_current := trim((t->'name')::TEXT, '"')||'_current';
  v_table_history := trim((t->'name')::TEXT, '"')||'_history';
  v_query := replace(v_query, '#history_table#', v_table_history);
  v_query := replace(v_query, '#current_table#', v_table_current);
  v_query := replace(v_query, '#record_type#', trim((t->'record_type')::TEXT, '"'));
  v_query := replace(v_query, '#where_current#', 'instance_id = '||instance_id||' AND datetime <@ '''||i_range::TEXT||'''::TSTZRANGE');
  v_query := replace(v_query, '#where_history#', 'instance_id = '||instance_id||' AND history_range && '''||i_range::TEXT||'''::TSTZRANGE');
  v_query := replace(v_query, '#tstzrange#', ''''||i_range::TEXT||'''::TSTZRANGE');
  RAISE NOTICE '%', v_query;
  RETURN QUERY EXECUTE v_query;
END;

$$;


CREATE OR REPLACE FUNCTION expand_data_by_dbname(i_name TEXT, i_range TSTZRANGE, instance_id INTEGER, dbname TEXT) RETURNS SETOF RECORD
LANGUAGE plpgsql
AS $$

DECLARE
  t JSON;
  v_query TEXT;
  v_table_current TEXT;
  v_table_history TEXT;
BEGIN

  SELECT metric_tables_config()->i_name INTO t;
  v_query := t->>'expand';
  v_table_current := trim((t->'name')::TEXT, '"')||'_current';
  v_table_history := trim((t->'name')::TEXT, '"')||'_history';
  v_query := replace(v_query, '#history_table#', v_table_history);
  v_query := replace(v_query, '#current_table#', v_table_current);
  v_query := replace(v_query, '#record_type#', trim((t->'record_type')::TEXT, '"'));
  v_query := replace(v_query, '#where_current#', 'instance_id = '||instance_id||' AND dbname = '||quote_literal(dbname)||' AND datetime <@ '''||i_range::TEXT||'''::TSTZRANGE');
  v_query := replace(v_query, '#where_history#', 'instance_id = '||instance_id||' AND dbname = '||quote_literal(dbname)||' AND history_range && '''||i_range::TEXT||'''::TSTZRANGE');
  v_query := replace(v_query, '#tstzrange#', ''''||i_range::TEXT||'''::TSTZRANGE');
  RAISE NOTICE '%', v_query;
  RETURN QUERY EXECUTE v_query;
END;

$$;


CREATE OR REPLACE FUNCTION aggregate_data() RETURNS TABLE(tblname TEXT, nb_rows INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
  t JSON;
  v_agg_periods TEXT[] := array['30m', '6h'];
  v_agg_table TEXT;
  i_period TEXT;
  v_query TEXT;
  i INTEGER;
BEGIN
  -- Build and run 'aggregate' query for type of metric.
  FOR t IN SELECT metric_tables_config()->json_object_keys(metric_tables_config()) LOOP
    FOREACH i_period IN ARRAY v_agg_periods LOOP
      v_agg_table := trim((t->'name')::TEXT, '"')||'_'||i_period||'_current';
      v_query := replace(t->>'aggregate', '#agg_table#', v_agg_table);
      v_query := replace(v_query, '#interval#', i_period);
      v_query := replace(v_query, '#record_type#', t->>'record_type');
      v_query := replace(v_query, '#name#', t->>'name');
      EXECUTE v_query;
      GET DIAGNOSTICS i = ROW_COUNT;
      RETURN QUERY SELECT v_agg_table, i;
    END LOOP;
  END LOOP;
END;
$$;


CREATE OR REPLACE FUNCTION truncate_time(i_tstz TIMESTAMP WITH TIME ZONE, i_interval INTERVAL)
RETURNS TIMESTAMP WITH TIME ZONE
LANGUAGE plpgsql
AS $$
DECLARE
  r_tstz TIMESTAMP WITH TIME ZONE;
  v_interval_min INT;
BEGIN
  SELECT (EXTRACT(EPOCH FROM i_interval)/60)::INTEGER INTO v_interval_min;
  IF v_interval_min < 60 THEN
    SELECT date_trunc('hour', i_tstz) + i_interval*TRUNC(date_part('minutes', i_tstz) / v_interval_min) INTO r_tstz;
  ELSE
    SELECT date_trunc('day', i_tstz) + i_interval*TRUNC(date_part('hours', i_tstz) / (v_interval_min/60)::INTEGER) INTO r_tstz;
  END IF;
  RETURN r_tstz;
END;
$$;


CREATE OR REPLACE FUNCTION set_datetime_record(i_datetime TIMESTAMP WITH TIME ZONE, i_record ANYELEMENT)
RETURNS ANYELEMENT
LANGUAGE plpgsql
AS $$

DECLARE
  r_record RECORD;
BEGIN
  r_record := i_record;
  r_record.datetime := i_datetime;
  RETURN r_record;
END;

$$;

CREATE OR REPLACE FUNCTION monitoring.insert_instance_availability(i_tstz TIMESTAMP WITH TIME ZONE, i_instance_id INTEGER, i_available BOOLEAN)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
  s_available BOOLEAN;
BEGIN
  SELECT available::BOOLEAN FROM monitoring.instance_availability
  WHERE instance_id = i_instance_id
  ORDER BY datetime desc LIMIT 1 INTO s_available;
  IF s_available IS NULL OR i_available <> s_available THEN
    INSERT INTO monitoring.instance_availability (datetime, instance_id, available)
    VALUES (i_tstz, i_instance_id, i_available);
  END IF;
END;
$$;

CREATE TABLE monitoring.instance_availability(datetime TIMESTAMP WITH TIME ZONE NOT NULL, instance_id INTEGER NOT NULL, available BOOLEAN NOT NULL);
CREATE INDEX idx_instance_availability ON monitoring.instance_availability (instance_id, datetime);

-- Create the tables if they don't exist
SELECT * FROM create_tables();

CREATE TABLE monitoring.collector_status (
  instance_id INTEGER PRIMARY KEY REFERENCES monitoring.instances(instance_id) ON DELETE CASCADE,
  last_pull TIMESTAMP WITHOUT TIME ZONE,
  last_push TIMESTAMP WITHOUT TIME ZONE,
  last_insert TIMESTAMP WITHOUT TIME ZONE,
  status CHAR(12) CHECK (status = 'OK' OR status = 'FAIL')
);

GRANT ALL ON SCHEMA monitoring TO temboard;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA monitoring TO temboard;
GRANT ALL ON ALL TABLES IN SCHEMA monitoring TO temboard;
GRANT ALL ON ALL SEQUENCES IN SCHEMA monitoring TO temboard;
