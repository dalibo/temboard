BEGIN;

SET search_path TO monitoring;

-- add 'ON DELETE CASCADE' to foreign key constraints for metrics tables
DO $$
  DECLARE
    r record;
    metric TEXT;
    metrics TEXT[] := array[
      'metric_sessions',
      'metric_xacts',
      'metric_locks',
      'metric_blocks',
      'metric_bgwriter',
      'metric_db_size',
      'metric_tblspc_size',
      'metric_filesystems_size',
      'metric_temp_files_size_delta',
      'metric_wal_files',
      'metric_cpu',
      'metric_process',
      'metric_memory',
      'metric_loadavg',
      'metric_vacuum_analyze',
      'metric_replication_lag',
      'metric_replication_connection',
      'metric_heap_bloat',
      'metric_btree_bloat'
    ];
  BEGIN
    FOREACH metric IN ARRAY metrics LOOP
      FOR r IN
        SELECT
          tc.table_schema,
          tc.constraint_name,
          tc.table_name,
          kcu.column_name,
          ccu.table_schema AS foreign_table_schema,
          ccu.table_name AS foreign_table_name,
          ccu.column_name AS foreign_column_name
        FROM
          information_schema.table_constraints AS tc
          JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
          JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name like metric || '%'
      LOOP
        RAISE NOTICE 'DROPING AND CREATING CONSTRAINT %', r.constraint_name;
        EXECUTE 'ALTER TABLE ' || quote_ident(r.table_name)|| ' DROP CONSTRAINT '|| quote_ident(r.constraint_name) || ';';
        EXECUTE 'ALTER TABLE ' || quote_ident(r.table_name) || ' ADD CONSTRAINT ' || r.constraint_name || ' FOREIGN KEY (' || quote_ident(r.column_name) || ') REFERENCES ' || quote_ident(r.foreign_table_name) || '(' || r.foreign_column_name || ') ON DELETE CASCADE;';
      END LOOP;
    END LOOP;
  END$$;

-- add 'ON DELETE RESTRICT' on host_id foreign key for table 'instances'
DO $$
  DECLARE constraint_name TEXT;
  BEGIN
    SELECT tc.constraint_name INTO constraint_name
    FROM
      information_schema.table_constraints AS tc
      JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
      WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = 'instances' AND kcu.column_name = 'host_id';
    RAISE NOTICE 'DROPING AND CREATING CONSTRAINT %', constraint_name;
    EXECUTE 'ALTER TABLE instances DROP CONSTRAINT ' || quote_ident(constraint_name) || ';';
    EXECUTE 'ALTER TABLE instances ADD CONSTRAINT ' || quote_ident(constraint_name) || ' FOREIGN KEY (host_id) REFERENCES hosts(host_id) ON DELETE RESTRICT;';
  END $$;

-- add 'ON DELETE CASCADE' for instance_id foreign keys of checks table
DO $$
  DECLARE r record;
  BEGIN
    FOR r IN
      SELECT
        tc.table_schema,
        tc.constraint_name,
        tc.table_name,
        kcu.column_name,
        ccu.table_schema AS foreign_table_schema,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
      FROM
        information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
      WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = 'checks'
    LOOP
      RAISE NOTICE 'DROPING AND CREATING CONSTRAINT %', r.constraint_name;
      EXECUTE 'ALTER TABLE checks DROP CONSTRAINT '|| quote_ident(r.constraint_name) || ';';
      EXECUTE 'ALTER TABLE checks ADD CONSTRAINT ' || r.constraint_name || ' FOREIGN KEY (' || quote_ident(r.column_name) || ') REFERENCES ' || quote_ident(r.foreign_table_name) || '(' || r.foreign_column_name || ') ON DELETE CASCADE;';
    END LOOP;
  END $$;

-- add 'ON DELETE CASCADE' for foreign keys of checks related tables
DO $$
  DECLARE
    r record;
    constraint_name TEXT;
    table_name_ TEXT;
    tables TEXT[] := array[
      'check_states',
      'state_changes',
      'check_changes'
    ];
  BEGIN
    FOREACH table_name_ IN ARRAY tables LOOP
      SELECT tc.constraint_name INTO constraint_name
      FROM
        information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
      WHERE tc.constraint_type =  'FOREIGN KEY' AND tc.table_name = table_name_ AND kcu.column_name = 'check_id';
      RAISE NOTICE 'DROPING AND CREATING CONSTRAINT %', constraint_name;
      EXECUTE 'ALTER TABLE ' || quote_ident(table_name_) || ' DROP CONSTRAINT ' || quote_ident(constraint_name) || ';';
      EXECUTE 'ALTER TABLE ' || quote_ident(table_name_) || ' ADD CONSTRAINT ' || quote_ident(constraint_name) || ' FOREIGN KEY (check_id) REFERENCES checks(check_id) ON DELETE CASCADE;';
    END LOOP;
  END$$;

-- Purge obsolete monitoring data
-- ie. remove any data which corresponds to previously removed instances
DO $$
  DECLARE
    r record;
  BEGIN
    FOR r in
      SELECT mi.instance_id, mh.host_id
        FROM monitoring.instances AS mi
        JOIN monitoring.hosts as mh ON mh.host_id = mi.host_id
        WHERE (port, hostname) NOT IN (select pg_port, hostname from application.instances)
    LOOP
      RAISE NOTICE 'Droping data for instance %', r.instance_id;
      EXECUTE 'DELETE FROM instances WHERE instance_id = ' || r.instance_id;
    END LOOP;
  END$$;

-- Now remove any information about a host if there's no instance left for this
-- host
DO $$
  DECLARE
    r record;
  BEGIN
    FOR r in
      SELECT mh.host_id
        FROM monitoring.hosts as mh
        WHERE host_id NOT IN (select host_id from instances)
    LOOP
      RAISE NOTICE 'Droping host %', r.host_id;
      EXECUTE 'DELETE FROM hosts WHERE host_id = ' || r.host_id;
    END LOOP;
  END$$;


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


COMMIT;
