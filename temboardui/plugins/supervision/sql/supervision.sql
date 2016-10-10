drop schema if exists supervision cascade;
create schema supervision;
SET search_path TO supervision, public;

-- A host is something running an operating system, it can be physical
-- or virtual. The primary key being the hostname it must be fully
-- qualified.
create table hosts (
  hostname text primary key, -- fqdn
  os text not null, -- kernel name
  os_version text not null, -- kernel version
  os_flavour text, -- distribution
  cpu_count integer, 
  cpu_arch text,
  memory_size bigint,
  swap_size bigint,
  virtual boolean
);

-- Instances are defined as running postgres processed that listen to
-- a specific TCP port
create table instances (
  hostname text not null references hosts (hostname),
  port integer not null,
  local_name text not null, -- name of the instance inside the agent configuration
  version text not null, -- dotted minor version
  version_num integer not null, -- for comparisons (e.g. 90401)
  data_directory text not null,
  sysuser text, -- system user
  standby boolean not null default false,
  primary key (hostname, port)
);

-- Metrics tables

-- Sessions. Number of backends by type. Summing all counters gives
-- the total number of backends
create table metric_sessions (
  datetime timestamptz not null,
  hostname text not null,
  port integer not null,
  dbname text not null,
  active integer not null,
  waiting integer not null,
  idle integer not null,
  idle_in_xact integer not null,
  idle_in_xact_aborted integer not null,
  fastpath integer not null,
  disabled integer not null,
  no_priv integer not null,
  foreign key (hostname, port) references instances (hostname, port),
  primary key (datetime, hostname, port, dbname)
);

-- Transactions. Values are deltas over measure_interval.
create table metric_xacts (
  datetime timestamptz not null,
  hostname text not null,
  port integer not null,
  dbname text not null,
  foreign key (hostname, port) references instances (hostname, port),
  primary key (datetime, hostname, port, dbname),
  measure_interval interval not null,
  n_commit bigint not null,
  n_rollback bigint not null
);

-- Locks. Number of locks by mode and acquisition
create table metric_locks (
  datetime timestamptz not null,
  hostname text not null,
  port integer not null,
  dbname text not null,
  foreign key (hostname, port) references instances (hostname, port),
  primary key (datetime, hostname, port, dbname),
  access_share integer not null,
  row_share integer not null,
  row_exclusive integer not null,
  share_update_exclusive integer not null,
  share integer not null,
  share_row_exclusive integer not null,
  exclusive integer not null,
  access_exclusive integer not null,
  siread integer not null,
  waiting_access_share integer not null,
  waiting_row_share integer not null,
  waiting_row_exclusive integer not null,
  waiting_share_update_exclusive integer not null,
  waiting_share integer not null,
  waiting_share_row_exclusive integer not null,
  waiting_exclusive integer not null,
  waiting_access_exclusive integer not null
);

-- Per database read I/O. Values are deltas over measure_interval
create table metric_blocks (
  datetime timestamptz not null,
  hostname text not null,
  port integer not null,
  dbname text not null,
  measure_interval interval not null,
  blks_read bigint not null,
  blks_hit bigint not null,
  hitmiss_ratio float not null,
  foreign key (hostname, port) references instances (hostname, port),
  primary key (datetime, hostname, port, dbname)
);

-- Per instance write I/O and checkpoint from pg_stat_bgwriter. Deltas
-- over measure_interval to compute frequencies.
create table metric_bgwriter (
  datetime timestamptz not null,
  hostname text not null,
  port integer not null,
  foreign key (hostname, port) references instances (hostname, port),
  primary key (datetime, hostname, port),
  measure_interval interval not null,
  checkpoints_timed bigint not null,
  checkpoints_req bigint not null,
  checkpoint_write_time double precision,
  checkpoint_sync_time double precision,
  buffers_checkpoint bigint not null,
  buffers_clean bigint not null,
  maxwritten_clean bigint not null,
  buffers_backend bigint not null,
  buffers_backend_fsync bigint,
  buffers_alloc bigint not null,
  stats_reset timestamptz
);

-- Database sizes
create table metric_db_size (
  datetime timestamptz not null,
  hostname text not null,
  port integer not null,
  dbname text not null,
  foreign key (hostname, port) references instances (hostname, port),
  primary key (datetime, hostname, port, dbname),
  size bigint not null -- in bytes
);

-- Tablespace sizes
create table metric_tblspc_size (
  datetime timestamptz not null,
  hostname text not null,
  port integer not null,
  spcname text not null,
  foreign key (hostname, port) references instances (hostname, port),
  primary key (datetime, hostname, port, spcname),
  size bigint not null -- in bytes
);

-- Filesystems disk usage in bytes
create table metric_filesystems_size (
  datetime timestamptz not null,
  hostname text not null,
  mount_point text not null,
  foreign key (hostname) references hosts (hostname),
  primary key (datetime, hostname, mount_point),
  used bigint not null,
  total bigint not null,
  device text not null
);

-- Temp files total size when stored at tablespace level (from 8.3 to 9.1)
create table metric_temp_files_size_tblspc (
  datetime timestamptz not null,
  hostname text not null,
  port integer not null,
  spcname text not null,
  foreign key (hostname, port) references instances (hostname, port),
  primary key (datetime, hostname, port, spcname),
  size bigint not null
);

-- Temp files total size when stored at database level (8.2 and older, 9.2 and latter)
create table metric_temp_files_size_db (
  datetime timestamptz not null,
  hostname text not null,
  port integer not null,
  dbname text not null,
  foreign key (hostname, port) references instances (hostname, port),
  primary key (datetime, hostname, port, dbname),
  size bigint not null
);

-- WAL files activity.
create table metric_wal_files (
  datetime timestamptz not null,
  hostname text not null,
  port integer not null,
  foreign key (hostname, port) references instances (hostname, port),
  primary key (datetime, hostname, port),
  measure_interval interval not null,
  written_size bigint not null, -- delta
  current_location text not null,
  total integer not null,
  archive_ready integer not null,
  total_size bigint not null
);

create table metric_cpu (
  datetime timestamptz not null,
  hostname text not null,
  cpu text not null,
  foreign key (hostname) references hosts (hostname),
  primary key (datetime, hostname, cpu),
  measure_interval interval not null,
  -- time_* are in milliseconds
  time_user integer not null, -- user + nice from /proc/stat
  time_system integer not null, -- system + irq + softirq from /proc/stat
  time_idle integer not null,
  time_iowait integer not null,
  time_steal integer not null
);

create table metric_process (
  datetime timestamptz not null,
  hostname text not null,
  foreign key (hostname) references hosts (hostname),
  primary key (datetime, hostname),
  measure_interval interval not null,
  context_switches bigint not null,
  forks bigint not null,
  -- following are not deltas
  procs_running integer not null,
  procs_blocked integer not null,
  procs_total integer not null
);

-- RAM + SWAP in bytes
create table metric_memory (
  datetime timestamptz not null,
  hostname text not null,
  foreign key (hostname) references hosts (hostname),
  primary key (datetime, hostname),
  mem_total bigint not null,
  mem_used bigint not null,
  mem_free bigint not null,
  mem_buffers bigint not null,
  mem_cached bigint not null,
  swap_total bigint not null,
  swap_used bigint not null
);

-- Load average
create table metric_loadavg (
  datetime timestamptz not null,
  hostname text not null,
  foreign key (hostname) references hosts (hostname),
  primary key (datetime, hostname),
  load1 float not null,
  load5 float not null,
  load15 float not null
);

-- Number of vacuum and analyze (manual or auto) per database. Values
-- are deltas over measure_interval
create table metric_vacuum_analyze (
  datetime timestamptz not null,
  hostname text not null,
  port integer not null,
  dbname text not null,
  foreign key (hostname, port) references instances (hostname, port),
  primary key (datetime, hostname, port, dbname),
  measure_interval interval not null,
  n_vacuum integer not null,
  n_analyze integer not null,
  n_autovacuum integer not null,
  n_autoanalyze integer not null
);

-- Replication WAL addresses to compute lag between primary and
-- standby servers inside a cluster
create table metric_replication (
  datetime timestamptz not null,
  hostname text not null,
  port integer not null,
  foreign key (hostname, port) references instances (hostname, port),
  primary key (datetime, hostname, port),
  receive_location text not null,
  replay_location text not null
);

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

CREATE OR REPLACE FUNCTION metric_configuration() RETURNS TABLE(tablename TEXT, agg_query TEXT, insert_agg_query TEXT)
LANGUAGE plpgsql AS $$
DECLARE
BEGIN
	RETURN QUERY SELECT
					'metric_db_size'::TEXT,
					'SELECT #trunc_function#(datetime) AS datetime, hostname, port, dbname, (SUM(size)/COUNT(*))::BIGINT AS size, COUNT(*) AS w FROM #tablename# #where# GROUP BY 1,2,3,4 ORDER BY 1,2,3,4'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname, port, dbname) DO UPDATE SET size = EXCLUDED.size, w = EXCLUDED.w WHERE #tablename#.w < EXCLUDED.w'::TEXT;
	RETURN QUERY SELECT
					'metric_loadavg'::TEXT,
					'SELECT #trunc_function#(datetime) AS datetime, hostname, round(avg(load1)::numeric, 2) AS load1, round(avg(load5)::numeric, 2) AS load5, round(avg(load15)::numeric, 2) AS load15, COUNT(*) AS w FROM #tablename# #where# GROUP BY 1,2 ORDER BY 1'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname) DO UPDATE SET load1 = EXCLUDED.load1, load5 = EXCLUDED.load5, load15 = EXCLUDED.load15, w = EXCLUDED.w WHERE #tablename#.w < EXCLUDED.w'::TEXT;

	RETURN QUERY SELECT
					'metric_bgwriter'::TEXT,
					'SELECT #trunc_function#(datetime) AS datetime, hostname, port, SUM(measure_interval) AS measure_interval, SUM(checkpoints_timed) AS checkpoints_timed, SUM(checkpoints_req) AS checkpoints_req, SUM(checkpoint_write_time) AS checkpoint_write_time, SUM(checkpoint_sync_time) AS checkpoint_sync_time, SUM(buffers_checkpoint) AS buffers_checkpoint, SUM(buffers_clean) AS buffers_clean, SUM(maxwritten_clean) AS maxwritten_clean, SUM(buffers_backend) AS buffers_backend, SUM(buffers_backend_fsync) AS buffers_backend_fsync, SUM(buffers_alloc) AS buffers_alloc FROM #tablename# #where# GROUP BY 1, 2, 3 ORDER BY 1,2,3'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname, port) DO UPDATE SET measure_interval = EXCLUDED.measure_interval, checkpoints_timed = EXCLUDED.checkpoints_timed, checkpoints_req = EXCLUDED.checkpoints_req, checkpoint_write_time = EXCLUDED.checkpoint_write_time, checkpoint_sync_time = EXCLUDED.checkpoint_sync_time, buffers_checkpoint = EXCLUDED.buffers_checkpoint, buffers_clean = EXCLUDED.buffers_clean, maxwritten_clean = EXCLUDED.maxwritten_clean, buffers_backend = EXCLUDED.buffers_backend, buffers_backend_fsync = EXCLUDED.buffers_backend_fsync, buffers_alloc = EXCLUDED.buffers_alloc WHERE #tablename#.measure_interval < EXCLUDED.measure_interval'::TEXT;

	RETURN QUERY SELECT
					'metric_blocks'::TEXT,
					'SELECT #trunc_function#(datetime) AS datetime, hostname, port, dbname, SUM(measure_interval) AS measure_interval, SUM(blks_read) AS blks_read, SUM(blks_hit) AS blks_hit, SUM(hitmiss_ratio)/COUNT(*) AS hitmiss_ratio, COUNT(*) AS w FROM #tablename# #where# GROUP BY 1,2,3,4 ORDER BY 1,2,3,4'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname, port, dbname) DO UPDATE SET measure_interval = EXCLUDED.measure_interval, blks_read = EXCLUDED.blks_read, blks_hit = EXCLUDED.blks_hit, hitmiss_ratio = EXCLUDED.hitmiss_ratio WHERE #tablename#.measure_interval < EXCLUDED.measure_interval'::TEXT;

	RETURN QUERY SELECT
					'metric_cpu'::TEXT,
					'SELECT #trunc_function#(datetime) AS datetime, hostname, cpu, SUM(measure_interval) AS measure_interval, SUM(time_user) AS time_user, SUM(time_system) AS time_system, SUM(time_idle) AS time_idle, SUM(time_iowait) AS time_iowait, SUM(time_steal) AS time_steal FROM #tablename# #where# GROUP BY 1,2,3'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname, cpu) DO UPDATE SET measure_interval = EXCLUDED.measure_interval, time_user = EXCLUDED.time_user, time_system = EXCLUDED.time_system, time_iowait = EXCLUDED.time_iowait, time_steal = EXCLUDED.time_steal WHERE #tablename#.measure_interval < EXCLUDED.measure_interval'::TEXT;

	RETURN QUERY SELECT
					'metric_sessions'::TEXT,
					'SELECT #trunc_function#(datetime) AS datetime, hostname, port, dbname, SUM(active)/COUNT(*) AS active, SUM(waiting)/COUNT(*) AS waiting, SUM(idle)/COUNT(*) AS idle, SUM(idle_in_xact)/COUNT(*) AS idle_in_xact, SUM(idle_in_xact_aborted)/COUNT(*) AS idle_in_xact_aborted, SUM(fastpath)/COUNT(*) AS fastpath, SUM(disabled)/COUNT(*) AS disabled, SUM(no_priv)/COUNT(*) AS no_priv, COUNT(*) AS w FROM #tablename# #where# GROUP BY 1,2,3,4 ORDER BY 1,2,3,4'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname, port, dbname) DO UPDATE SET w = EXCLUDED.w, active = EXCLUDED.active, waiting = EXCLUDED.waiting, idle = EXCLUDED.idle, idle_in_xact = EXCLUDED.idle_in_xact, idle_in_xact_aborted = EXCLUDED.idle_in_xact_aborted, fastpath = EXCLUDED.fastpath, disabled = EXCLUDED.disabled, no_priv = EXCLUDED.no_priv WHERE #tablename#.w < EXCLUDED.w'::TEXT;
	RETURN QUERY SELECT
					'metric_xacts'::TEXT,
					'SELECT #trunc_function#(datetime) AS datetime, hostname, port, dbname, SUM(measure_interval) AS measure_interval, SUM(n_commit) AS n_commit, SUM(n_rollback) AS n_rollback, COUNT(*) AS w FROM #tablename# #where# GROUP BY 1,2,3,4'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname, port, dbname) DO UPDATE SET w = EXCLUDED.w, measure_interval = EXCLUDED.measure_interval, n_commit = EXCLUDED.n_commit, n_rollback = EXCLUDED.n_rollback WHERE #tablename#.w < EXCLUDED.w'::TEXT;
	RETURN QUERY SELECT
					'metric_locks'::TEXT,
					'SELECT #trunc_function#(datetime) AS datetime, hostname, port, dbname, avg(access_share) AS access_share, avg(row_share) AS row_share, avg(row_exclusive) AS row_exclusive, avg(share_update_exclusive) AS share_update_exclusive, avg(share) AS share, avg(share_row_exclusive) AS share_row_exclusive, avg(exclusive) AS exclusive, avg(access_exclusive) AS access_exclusive, avg(siread) AS siread, avg(waiting_access_share) AS waiting_access_share, avg(waiting_row_share) AS waiting_row_share, avg(waiting_row_exclusive) AS waiting_row_exclusive, avg(waiting_share_update_exclusive) AS waiting_share_update_exclusive, avg(waiting_share) AS waiting_share, avg(waiting_share_row_exclusive) AS waiting_share_row_exclusive, avg(waiting_exclusive) AS waiting_exclusive, avg(waiting_access_exclusive) AS waiting_access_exclusive, COUNT(*) AS w FROM #tablename# #where# GROUP BY 1,2,3,4 ORDER BY 1,2,3,4'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname, port, dbname) DO UPDATE SET w = EXCLUDED.w, access_share = EXCLUDED.access_share, row_share = EXCLUDED.row_share, row_exclusive = EXCLUDED.row_exclusive, share_update_exclusive = EXCLUDED.share_update_exclusive, share = EXCLUDED.share, share_row_exclusive = EXCLUDED.share_row_exclusive, exclusive = EXCLUDED.exclusive, access_exclusive = EXCLUDED.access_exclusive, siread = EXCLUDED.siread, waiting_access_share = EXCLUDED.waiting_access_share, waiting_row_share = EXCLUDED.waiting_row_share, waiting_row_exclusive = EXCLUDED.waiting_row_exclusive, waiting_share_update_exclusive = EXCLUDED.waiting_share_update_exclusive, waiting_share = EXCLUDED.waiting_share, waiting_share_row_exclusive = EXCLUDED.waiting_share_row_exclusive, waiting_exclusive = EXCLUDED.waiting_exclusive, waiting_access_exclusive = EXCLUDED.waiting_access_exclusive  WHERE #tablename#.w < EXCLUDED.w'::TEXT;
	RETURN QUERY SELECT
					'metric_tblspc_size'::TEXT,
					'SELECT #trunc_function#(datetime) AS datetime, hostname, port, spcname, avg(size) AS size, COUNT(*) AS w FROM #tablename# #where# GROUP BY 1,2,3,4 ORDER BY 1,2,3,4'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname, port, spcname) DO UPDATE SET w = EXCLUDED.w, size = EXCLUDED.size WHERE #tablename#.w < EXCLUDED.w'::TEXT;
	RETURN QUERY SELECT
					'metric_filesystems_size'::TEXT,
					'SELECT #trunc_function#(datetime), hostname, mount_point, avg(used) AS used, avg(total) AS total, COUNT(*) AS w FROM #tablename# #where# GROUP BY 1,2,3 ORDER BY 1,2,3'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname, mount_point) DO UPDATE SET w = EXCLUDED.w, used = EXCLUDED.used, total = EXCLUDED.total WHERE #tablename#.w < EXCLUDED.w'::TEXT;
	RETURN QUERY SELECT
					'metric_temp_files_size_tblspc'::TEXT,
					'SELECT #trunc_function#(datetime) AS datetime, hostname, port, spcname, avg(size) AS size, COUNT(*) AS w FROM #tablename# #where# GROUP BY 1,2,3,4 ORDER BY 1,2,3,4'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname, port, spcname) DO UPDATE SET w = EXCLUDED.w, size = EXCLUDED.size WHERE #tablename#.w < EXCLUDED.w'::TEXT;
	RETURN QUERY SELECT
					'metric_temp_files_size_db'::TEXT,
					'SELECT #trunc_function#(datetime) AS datetime, hostname, port, dbname, avg(size) AS size, COUNT(*) AS w FROM #tablename# #where# GROUP BY 1,2,3,4 ORDER BY 1,2,3,4'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname, port, dbname) DO UPDATE SET w = EXCLUDED.w, size = EXCLUDED.size WHERE #tablename#.w < EXCLUDED.w'::TEXT;
	RETURN QUERY SELECT
					'metric_wal_files'::TEXT,
					'SELECT #trunc_function#(datetime) AS datetime, hostname, port, SUM(measure_interval) AS measure_interval, MAX(written_size) AS written_size, MIN(current_location::pg_lsn)::TEXT AS current_location, MAX(total) AS total, MAX(archive_ready) AS archive_ready, MAX(total_size) AS total_size FROM #tablename# #where# GROUP BY 1,2,3 ORDER BY 1,2,3'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname, port) DO UPDATE SET measure_interval = EXCLUDED.measure_interval, written_size = EXCLUDED.written_size, total = EXCLUDED.total, archive_ready = EXCLUDED.archive_ready, total_size = EXCLUDED.total_size, current_location = EXCLUDED.current_location WHERE #tablename#.measure_interval < EXCLUDED.measure_interval'::TEXT;
	RETURN QUERY SELECT
					'metric_process'::TEXT,
					'SELECT #trunc_function#(datetime) AS datetime, hostname, SUM(measure_interval) AS measure_interval, SUM(context_switches) AS context_switches, SUM(forks) AS forks, avg(procs_running) AS procs_running, avg(procs_blocked) AS procs_blocked, avg(procs_total) AS procs_total, COUNT(*) AS w FROM #tablename# #where# GROUP BY 1,2 ORDER BY 1,2'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname) DO UPDATE SET measure_interval = EXCLUDED.measure_interval, context_switches = EXCLUDED.context_switches, forks = EXCLUDED.forks, procs_running = EXCLUDED.procs_running, procs_blocked = EXCLUDED.procs_blocked, procs_total = EXCLUDED.procs_total, w = EXCLUDED.w WHERE #tablename#.w < EXCLUDED.w'::TEXT;
	RETURN QUERY SELECT
					'metric_memory'::TEXT,
					'SELECT #trunc_function#(datetime) AS datetime, hostname, avg(mem_total) AS mem_total, avg(mem_used) AS mem_used, avg(mem_free) AS mem_free, avg(mem_buffers) AS mem_buffers, avg(mem_cached) AS mem_cached, avg(swap_total) AS swap_total, avg(swap_used) AS swap_used, COUNT(*) AS w FROM #tablename# #where# GROUP BY 1,2 ORDER BY 1,2'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname) DO UPDATE SET mem_total = EXCLUDED.mem_total, mem_used = EXCLUDED.mem_used, mem_free = EXCLUDED.mem_free, mem_buffers = EXCLUDED.mem_buffers, mem_cached = EXCLUDED.mem_cached, swap_total = EXCLUDED.swap_total, swap_used = EXCLUDED.swap_used, w = EXCLUDED.w WHERE #tablename#.w < EXCLUDED.w'::TEXT;
	RETURN QUERY SELECT
					'metric_vacuum_analyze'::TEXT,
					'SELECT #trunc_function#(datetime) AS datetime, hostname, port, dbname, SUM(measure_interval) AS measure_interval, SUM(n_vacuum) AS n_vacuum, SUM(n_analyze) AS n_analyze, SUM(n_autovacuum) AS n_autovacuum, SUM(n_autoanalyze) AS n_autoanalyze FROM #tablename# #where# GROUP BY 1,2,3,4'::TEXT,
					'INSERT INTO #tablename# #agg_query# ON CONFLICT (datetime, hostname, port, dbname) DO UPDATE SET measure_interval = EXCLUDED.measure_interval, n_vacuum = EXCLUDED.n_vacuum, n_analyze = EXCLUDED.n_analyze, n_autovacuum = EXCLUDED.n_autovacuum, n_autoanalyze = EXCLUDED.n_autoanalyze WHERE #tablename#.measure_interval < EXCLUDED.measure_interval'::TEXT;
END;
$$;

CREATE OR REPLACE FUNCTION metric_create_agg_tables() RETURNS TABLE(created_table TEXT)
LANGUAGE plpgsql AS $$

DECLARE
	i_tablename TEXT;
	v_tablename_agg TEXT;
	v_agg_periods TEXT[] := array['10m', '30m', '4h'];
	i_period TEXT;
BEGIN
	FOR i_tablename IN SELECT tablename FROM metric_configuration() ORDER BY tablename LOOP
		FOREACH i_period IN ARRAY v_agg_periods LOOP
			v_tablename_agg := i_tablename||'_'||i_period;
			PERFORM 1 FROM pg_tables WHERE tablename = v_tablename_agg;
			IF NOT FOUND THEN
				EXECUTE 'CREATE TABLE '||v_tablename_agg||' (LIKE '||i_tablename||' INCLUDING ALL)';
				EXECUTE 'ALTER TABLE '||v_tablename_agg||' ADD COLUMN w INTEGER DEFAULT 1';
				RETURN QUERY SELECT v_tablename_agg;
			END IF;
		END LOOP;
	END LOOP;
END;

$$;

CREATE OR REPLACE FUNCTION metric_truncate_agg_tables() RETURNS TABLE(created_table TEXT)
LANGUAGE plpgsql AS $$

DECLARE
	i_tablename TEXT;
	v_tablename_agg TEXT;
	v_agg_periods TEXT[] := array['10m', '30m', '4h'];
	i_period TEXT;
BEGIN
	FOR i_tablename IN SELECT tablename FROM metric_configuration() ORDER BY tablename LOOP
		FOREACH i_period IN ARRAY v_agg_periods LOOP
			v_tablename_agg := i_tablename||'_'||i_period;
			PERFORM 1 FROM pg_tables WHERE tablename = v_tablename_agg;
			IF FOUND THEN
				EXECUTE 'TRUNCATE '||v_tablename_agg;
				RETURN QUERY SELECT v_tablename_agg;
			END IF;
		END LOOP;
	END LOOP;
END;

$$;


CREATE OR REPLACE FUNCTION metric_populate_agg_tables() RETURNS TABLE(agg_tablename TEXT, nb_insert BIGINT)
LANGUAGE plpgsql AS $$

DECLARE
	v_last_datetime TIMESTAMP WITH TIME ZONE;
	i_tablename TEXT;
	i_agg_query TEXT;
	v_agg_query TEXT;
	i_insert_agg_query TEXT;
	v_insert_agg_query TEXT;
	v_tablename_agg TEXT;
	v_agg_periods TEXT[] := array['10m', '30m', '4h'];
	v_interval TEXT;
	i_period TEXT;
	v_nb_insert BIGINT := 0;
	rec RECORD;
BEGIN
	PERFORM metric_create_agg_tables();
	FOR i_tablename, i_agg_query, i_insert_agg_query IN SELECT * FROM metric_configuration() ORDER BY tablename LOOP
		FOREACH i_period IN ARRAY v_agg_periods LOOP
			v_tablename_agg := i_tablename||'_'||i_period;
			IF i_period = '10m' THEN
				v_interval := '10 minutes';
			ELSIF i_period = '30m' THEN
				v_interval := '30 minutes';
			ELSE
				v_interval := '4 hours';
			END IF;
			PERFORM 1 FROM pg_tables WHERE tablename = v_tablename_agg;
			IF NOT FOUND THEN
				RAISE NOTICE 'Table % not found.', v_tablename_agg;
				CONTINUE;
			END IF;
			v_agg_query := replace(i_agg_query, '#trunc_function#', 'trunc_time_'||i_period);
			v_agg_query := replace(v_agg_query, '#tablename#', i_tablename);
			v_nb_insert := 0;

			RAISE NOTICE 'Populating % ...', v_tablename_agg;
			EXECUTE 'SELECT MAX(datetime) FROM '||v_tablename_agg INTO v_last_datetime ;
			IF v_last_datetime IS NULL THEN
				v_agg_query := replace(v_agg_query, '#where#', '');
			ELSE
				v_agg_query := replace(v_agg_query, '#where#', 'WHERE datetime >= ('''||v_last_datetime||'''::TIMESTAMP WITH TIME ZONE - INTERVAL '''||v_interval||''')');
			END IF;
			v_insert_agg_query := replace(i_insert_agg_query, '#tablename#', v_tablename_agg);
			v_insert_agg_query := replace(v_insert_agg_query, '#agg_query#', v_agg_query);
			RAISE DEBUG '%', v_insert_agg_query;
			EXECUTE v_insert_agg_query;
			IF FOUND THEN
				GET DIAGNOSTICS v_nb_insert = ROW_COUNT;
			END IF;
			RETURN QUERY SELECT v_tablename_agg, v_nb_insert;

		END LOOP;
	END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION trunc_time_10m(TIMESTAMP WITH TIME ZONE)
RETURNS TIMESTAMP WITH TIME ZONE AS $$
  SELECT date_trunc('hour', $1) + INTERVAL '10 min' * TRUNC(date_part('minute', $1) / 10)
$$ LANGUAGE SQL IMMUTABLE;

CREATE OR REPLACE FUNCTION trunc_time_30m(TIMESTAMP WITH TIME ZONE)
RETURNS TIMESTAMP WITH TIME ZONE AS $$
  SELECT date_trunc('hour', $1) + INTERVAL '30 min' * TRUNC(date_part('minute', $1) / 30)
$$ LANGUAGE SQL IMMUTABLE;

CREATE OR REPLACE FUNCTION trunc_time_4h(TIMESTAMP WITH TIME ZONE)
RETURNS TIMESTAMP WITH TIME ZONE AS $$
  SELECT date_trunc('day', $1) + INTERVAL '4 hours' * TRUNC(date_part('hours', $1) / 4)
$$ LANGUAGE SQL IMMUTABLE;
