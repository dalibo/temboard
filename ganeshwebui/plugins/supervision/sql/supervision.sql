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
  agent_key text,
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
  buffers_alloc bigint not null
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
  total bigint not null
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

CREATE MATERIALIZED VIEW mv_metric_loadavg_h(datetime, hostname, load1, load5, load15, w) AS SELECT date_trunc('hour', datetime) AS datetime, hostname, SUM(load1)/COUNT(*) AS load1, SUM(load5)/COUNT(*) AS load5, SUM(load15)/COUNT(*) AS load15, COUNT(*) FROM metric_loadavg GROUP BY date_trunc('hour', datetime), hostname ORDER BY date_trunc('hour', datetime);


CREATE UNIQUE INDEX i_mv_metric_loadavg_h_datetime_hostname ON mv_metric_loadavg_h (datetime, hostname);

CREATE MATERIALIZED VIEW mv_metric_loadavg_d(datetime, hostname, load1, load5, load15, w) AS SELECT date_trunc('day', datetime) AS datetime, hostname, SUM(load1)/SUM(w) AS load1, SUM(load5)/SUM(w) AS load5, SUM(load15)/SUM(w) AS load15, SUM(w) AS w FROM (SELECT datetime, hostname, load1*w AS load1, load5*w AS load5, load15*w AS load15, w FROM mv_metric_loadavg_h) AS sq1 GROUP BY date_trunc('day', datetime), hostname;

CREATE UNIQUE INDEX i_mv_metric_loadavg_d_datetime_hostname ON mv_metric_loadavg_d (datetime, hostname);

CREATE MATERIALIZED VIEW mv_metric_sessions_h(datetime, hostname, port, dbname, active, waiting, idle, idle_in_xact, idle_in_xact_aborted, fastpath, disabled, no_priv, w) AS SELECT date_trunc('hour', datetime) AS datetime, hostname, port, dbname, SUM(active)/COUNT(*) AS active, SUM(waiting)/COUNT(*) AS waiting, SUM(idle)/COUNT(*) AS idle, SUM(idle_in_xact)/COUNT(*) AS idle_in_xact, SUM(idle_in_xact_aborted)/COUNT(*) AS idle_in_xact_aborted, SUM(fastpath)/COUNT(*) AS fastpath, SUM(disabled)/COUNT(*) AS disabled, SUM(no_priv)/COUNT(*) AS no_priv, COUNT(*) FROM metric_sessions GROUP BY date_trunc('hour', datetime), hostname, port, dbname ORDER BY date_trunc('hour', datetime);

CREATE UNIQUE INDEX i_mv_metric_session_h_datetime_hostname_port_dbname ON mv_metric_sessions_h(datetime, hostname, port, dbname);

CREATE MATERIALIZED VIEW mv_metric_sessions_d(datetime, hostname, port, dbname, active, waiting, idle, idle_in_xact, idle_in_xact_aborted, fastpath, disabled, no_priv, w) AS  SELECT date_trunc('day', datetime) AS datetime, hostname, port, dbname, (SUM(active)/SUM(w))::BIGINT AS active, (SUM(waiting)/SUM(w))::BIGINT AS waiting, (SUM(idle)/SUM(w))::BIGINT AS idle, (SUM(idle_in_xact)/SUM(w))::BIGINT AS idle_in_xact, (SUM(idle_in_xact_aborted)/SUM(w))::BIGINT AS idle_in_xact_aborted, (SUM(fastpath)/SUM(w))::BIGINT AS fastpath, (SUM(disabled)/SUM(w))::BIGINT AS disabled, (SUM(no_priv)/SUM(w))::BIGINT AS no_priv, SUM(w) AS w FROM (SELECT datetime, hostname, port, dbname, active*w AS active, waiting*w AS waiting, idle*w AS idle, idle_in_xact*w AS idle_in_xact, idle_in_xact_aborted*w AS idle_in_xact_aborted, fastpath*w AS fastpath, disabled*w AS disabled, no_priv*w AS no_priv, w FROM mv_metric_sessions_h) AS sq1 GROUP BY date_trunc('day', datetime), hostname, port, dbname;

CREATE UNIQUE INDEX i_mv_metric_session_d_datetime_hostname_port_dbname ON mv_metric_sessions_d(datetime, hostname, port, dbname);

CREATE MATERIALIZED VIEW mv_metric_blocks_h(datetime, hostname, port, dbname, measure_interval, blks_read, blks_hit, hitmiss_ratio, w) AS SELECT date_trunc('hour', datetime) AS datetime, hostname, port, dbname, SUM(measure_interval) AS measure_interval, SUM(blks_read) AS blks_read, SUM(blks_hit) AS blks_hit, SUM(hitmiss_ratio)/COUNT(*) AS hitmiss_ratio, COUNT(*) AS w FROM metric_blocks GROUP BY date_trunc('hour', datetime), hostname, port, dbname ORDER BY date_trunc('hour', datetime), hostname, port, dbname;

CREATE UNIQUE INDEX i_mv_metric_blocks_h_datetime_hostname_port_dbname ON mv_metric_blocks_h(datetime, hostname, port, dbname);


CREATE MATERIALIZED VIEW mv_metric_blocks_d(datetime, hostname, port, dbname, measure_interval, blks_read, blks_hit, hitmiss_ratio, w) AS SELECT date_trunc('day', datetime) AS datetime, hostname, port, dbname, SUM(measure_interval) AS measure_interval, SUM(blks_read) AS blks_read, SUM(blks_hit) AS blks_hit, SUM(hitmiss_ratio)/SUM(w) AS hitmiss_ratio, SUM(w) AS w FROM (SELECT datetime, hostname, port, dbname, measure_interval, blks_read, blks_hit, hitmiss_ratio*w AS hitmiss_ratio, w FROM mv_metric_blocks_h) AS sq1 GROUP BY date_trunc('day', datetime), hostname, port, dbname;

CREATE UNIQUE INDEX i_mv_metric_blocks_d_datetime_hostname_port_dbname ON mv_metric_blocks_d(datetime, hostname, port, dbname);


CREATE MATERIALIZED VIEW mv_metric_xacts_h(datetime, hostname, port, dbname, measure_interval, n_commit, n_rollback, w) AS SELECT date_trunc('hour', datetime) AS datetime, hostname, port, dbname, SUM(measure_interval) AS measure_interval, SUM(n_commit) AS n_commit, SUM(n_rollback) AS n_rollback, COUNT(*) AS w FROM metric_xacts GROUP BY date_trunc('hour', datetime), hostname, port, dbname;

CREATE UNIQUE INDEX i_mv_metric_xacts_h_datetime_hostname_port_dbname ON mv_metric_xacts_h(datetime, hostname, port, dbname);

CREATE MATERIALIZED VIEW mv_metric_xacts_d(datetime, hostname, port, dbname, measure_interval, n_commit, n_rollback, w) AS SELECT date_trunc('day', datetime) AS datetime, hostname, port, dbname, SUM(measure_interval) AS measure_interval, SUM(n_commit) AS n_commit, SUM(n_rollback) AS n_rollback, SUM(w) AS w FROM mv_metric_xacts_h GROUP BY date_trunc('day', datetime), hostname, port, dbname;

CREATE UNIQUE INDEX i_mv_metric_xacts_d_datetime_hostname_port_dbname ON mv_metric_xacts_d(datetime, hostname, port, dbname);

CREATE MATERIALIZED VIEW mv_metric_locks_h(datetime, hostname, port, dbname, access_share, row_share, row_exclusive, share_update_exclusive, share, share_row_exclusive, exclusive, access_exclusive, siread, waiting_access_share, waiting_row_share, waiting_row_exclusive, waiting_share_update_exclusive, waiting_share, waiting_share_row_exclusive, waiting_exclusive, waiting_access_exclusive, w) AS SELECT date_trunc('hour', datetime) AS datetime, hostname, port, dbname, (SUM(access_share)/COUNT(*))::BIGINT AS access_share, (SUM(row_share)/COUNT(*))::BIGINT AS row_share, (SUM(row_exclusive)/COUNT(*))::BIGINT AS row_exclusive, (SUM(share_update_exclusive)/COUNT(*))::BIGINT AS share_update_exclusive, (SUM(share)/COUNT(*))::BIGINT AS share, (SUM(share_row_exclusive)/COUNT(*))::BIGINT AS share_row_exclusive, (SUM(exclusive)/COUNT(*))::BIGINT AS exclusive, (SUM(access_exclusive)/COUNT(*))::BIGINT AS access_exclusive, (SUM(siread)/COUNT(*))::BIGINT AS siread, (SUM(waiting_access_share)/COUNT(*))::BIGINT AS waiting_access_share, (SUM(waiting_row_share)/COUNT(*))::BIGINT AS waiting_row_share, (SUM(waiting_row_exclusive)/COUNT(*))::BIGINT AS waiting_row_exclusive, (SUM(waiting_share_update_exclusive)/COUNT(*))::BIGINT AS waiting_share_update_exclusive, (SUM(waiting_share)/COUNT(*))::BIGINT AS waiting_share, (SUM(waiting_share_row_exclusive)/COUNT(*))::BIGINT AS waiting_share_row_exclusive, (SUM(waiting_exclusive)/COUNT(*))::BIGINT AS waiting_exclusive, (SUM(waiting_access_exclusive)/COUNT(*))::BIGINT AS waiting_access_exclusive, COUNT(*) AS w FROM metric_locks GROUP BY date_trunc('hour', datetime), hostname, port, dbname;

CREATE UNIQUE INDEX i_mv_metric_locks_h_datetime_hostname_port_dbname ON mv_metric_locks_h(datetime, hostname, port, dbname);

CREATE MATERIALIZED VIEW mv_metric_locks_d(datetime, hostname, port, dbname, access_share, row_share, row_exclusive, share_update_exclusive, share, share_row_exclusive, exclusive, access_exclusive, siread, waiting_access_share, waiting_row_share, waiting_row_exclusive, waiting_share_update_exclusive, waiting_share, waiting_share_row_exclusive, waiting_exclusive, waiting_access_exclusive, w) AS SELECT date_trunc('day', datetime) AS datetime, hostname, port, dbname, (SUM(access_share)/SUM(w))::BIGINT AS access_share, (SUM(row_share)/SUM(w))::BIGINT AS row_share, (SUM(row_exclusive)/SUM(w))::BIGINT AS row_exclusive, (SUM(share_update_exclusive)/SUM(w))::BIGINT AS share_update_exclusive, (SUM(share)/SUM(w))::BIGINT AS share, (SUM(share_row_exclusive)/SUM(w))::BIGINT AS share_row_exclusive, (SUM(exclusive)/SUM(w))::BIGINT AS exclusive, (SUM(access_exclusive)/SUM(w))::BIGINT AS access_exclusive, (SUM(siread)/SUM(w))::BIGINT AS siread, (SUM(waiting_access_share)/SUM(w))::BIGINT AS waiting_access_share, (SUM(waiting_row_share)/SUM(w))::BIGINT AS waiting_row_share, (SUM(waiting_row_exclusive)/SUM(w))::BIGINT AS waiting_row_exclusive, (SUM(waiting_share_update_exclusive)/SUM(w))::BIGINT AS waiting_share_update_exclusive, (SUM(waiting_share)/SUM(w))::BIGINT AS waiting_share, (SUM(waiting_share_row_exclusive)/SUM(w))::BIGINT AS waiting_share_row_exclusive, (SUM(waiting_exclusive)/SUM(w))::BIGINT AS waiting_exclusive, (SUM(waiting_access_exclusive)/SUM(w))::BIGINT AS waiting_access_exclusive, SUM(w) AS w FROM (SELECT datetime, hostname, port, dbname, access_share*w AS access_share, row_share*w AS row_share, row_exclusive*w AS row_exclusive, share_update_exclusive*w AS share_update_exclusive, share*w AS share, share_row_exclusive*w AS share_row_exclusive, exclusive*w AS exclusive, access_exclusive*w AS access_exclusive, siread*w AS siread, waiting_access_share*w AS waiting_access_share, waiting_row_share*w AS waiting_row_share, waiting_row_exclusive*w AS waiting_row_exclusive, waiting_share_update_exclusive*w AS waiting_share_update_exclusive, waiting_share*w AS waiting_share, waiting_share_row_exclusive*w AS waiting_share_row_exclusive, waiting_exclusive*w AS waiting_exclusive, waiting_access_exclusive*w AS waiting_access_exclusive, w FROM mv_metric_locks_h) AS sq1 GROUP BY date_trunc('day', datetime), hostname, port, dbname;

CREATE UNIQUE INDEX i_mv_metric_locks_d_datetime_hostname_port_dbname ON mv_metric_locks_d(datetime, hostname, port, dbname);


CREATE MATERIALIZED VIEW mv_metric_bgwriter_h (datetime, hostname, port, measure_interval, checkpoints_timed, checkpoints_req, checkpoint_write_time, checkpoint_sync_time, buffers_checkpoint, buffers_clean, maxwritten_clean, buffers_backend, buffers_backend_fsync, buffers_alloc) AS SELECT date_trunc('hour', datetime), hostname, port, SUM(measure_interval) AS measure_interval, SUM(checkpoints_timed) AS checkpoints_timed, SUM(checkpoints_req) AS checkpoints_req, SUM(checkpoint_write_time) AS checkpoint_write_time, SUM(checkpoint_sync_time) AS checkpoint_sync_time, SUM(buffers_checkpoint) AS buffers_checkpoint, SUM(buffers_clean) AS buffers_clean, SUM(maxwritten_clean) AS maxwritten_clean, SUM(buffers_backend) AS buffers_backend, SUM(buffers_backend_fsync) AS buffers_backend_fsync, SUM(buffers_alloc) AS buffers_alloc FROM metric_bgwriter GROUP BY date_trunc('hour', datetime), hostname, port;

CREATE UNIQUE INDEX i_mv_metric_bgwriter_h_datetime_hostname_port ON mv_metric_bgwriter_h(datetime, hostname, port);

CREATE MATERIALIZED VIEW mv_metric_bgwriter_d (datetime, hostname, port, measure_interval, checkpoints_timed, checkpoints_req, checkpoint_write_time, checkpoint_sync_time, buffers_checkpoint, buffers_clean, maxwritten_clean, buffers_backend, buffers_backend_fsync, buffers_alloc) AS SELECT date_trunc('day', datetime), hostname, port, SUM(measure_interval) AS measure_interval, SUM(checkpoints_timed) AS checkpoints_timed, SUM(checkpoints_req) AS checkpoints_req, SUM(checkpoint_write_time) AS checkpoint_write_time, SUM(checkpoint_sync_time) AS checkpoint_sync_time, SUM(buffers_checkpoint) AS buffers_checkpoint, SUM(buffers_clean) AS buffers_clean, SUM(maxwritten_clean) AS maxwritten_clean, SUM(buffers_backend) AS buffers_backend, SUM(buffers_backend_fsync) AS buffers_backend_fsync, SUM(buffers_alloc) AS buffers_alloc FROM mv_metric_bgwriter_h GROUP BY date_trunc('day', datetime), hostname, port;

CREATE UNIQUE INDEX i_mv_metric_bgwriter_d_datetime_hostname_port ON mv_metric_bgwriter_d(datetime, hostname, port);

CREATE MATERIALIZED VIEW mv_metric_db_size_h(datetime, hostname, port, dbname, size, w) AS SELECT date_trunc('hour', datetime), hostname, port, dbname, (SUM(size)/COUNT(*))::BIGINT AS size, COUNT(*) AS w FROM metric_db_size GROUP BY date_trunc('hour', datetime), hostname, port, dbname;

CREATE UNIQUE INDEX i_mv_metric_db_size_h_datetime_hostname_port_dbname ON mv_metric_db_size_h(datetime, hostname, port, dbname);

CREATE MATERIALIZED VIEW mv_metric_db_size_d(datetime, hostname, port, dbname, size, w) AS SELECT date_trunc('day', datetime), hostname, port, dbname, (SUM(size)/SUM(w))::BIGINT AS size, SUM(w) AS w FROM (SELECT datetime, hostname, port, dbname, size*w AS size, w FROM mv_metric_db_size_h) AS sq1 GROUP BY date_trunc('day', datetime), hostname, port, dbname;

CREATE UNIQUE INDEX i_mv_metric_db_size_d_datetime_hostname_port_dbname ON mv_metric_db_size_d(datetime, hostname, port, dbname);

CREATE MATERIALIZED VIEW mv_metric_tblspc_size_h(datetime, hostname, port, spcname, size, w) AS SELECT date_trunc('hour', datetime), hostname, port, spcname, (SUM(size)/COUNT(*))::BIGINT AS size, COUNT(*) AS w FROM metric_tblspc_size GROUP BY date_trunc('hour', datetime), hostname, port, spcname;

CREATE UNIQUE INDEX i_mv_metric_tblspc_size_h_datetime_hostname_port_spcname ON mv_metric_tblspc_size_h(datetime, hostname, port, spcname);

CREATE MATERIALIZED VIEW mv_metric_tblspc_size_d(datetime, hostname, port, spcname, size, w) AS SELECT date_trunc('day', datetime), hostname, port, spcname, (SUM(size)/SUM(w))::BIGINT AS size, SUM(w) AS w FROM (SELECT datetime, hostname, port, spcname, size*w AS size, w FROM mv_metric_tblspc_size_h) AS sq1 GROUP BY date_trunc('day', datetime), hostname, port, spcname;

CREATE UNIQUE INDEX i_mv_metric_tblspc_size_d_datetime_hostname_port_spcname ON mv_metric_tblspc_size_d(datetime, hostname, port, spcname);

CREATE MATERIALIZED VIEW mv_metric_filesystems_size_h(datetime, hostname, mount_point, used, total, w) AS SELECT date_trunc('hour', datetime), hostname, mount_point, (SUM(used)/COUNT(*))::BIGINT AS used, (SUM(total)/COUNT(*))::BIGINT AS total,  COUNT(*) AS w FROM metric_filesystems_size GROUP BY date_trunc('hour', datetime), hostname, mount_point;

CREATE UNIQUE INDEX i_mv_metric_filesystems_size_h_datetime_hostname_mount_point ON mv_metric_filesystems_size_h(datetime, hostname, mount_point);

CREATE MATERIALIZED VIEW mv_metric_filesystems_size_d(datetime, hostname, mount_point, used, total, w) AS SELECT date_trunc('day', datetime), hostname, mount_point, (SUM(used)/SUM(w))::BIGINT AS used, (SUM(total)/SUM(w))::BIGINT AS total, SUM(w) AS w FROM (SELECT datetime, hostname, mount_point, used*w AS used, total*w AS total, w FROM mv_metric_filesystems_size_h) AS sq1 GROUP BY date_trunc('day', datetime), hostname, mount_point;

CREATE UNIQUE INDEX i_mv_metric_filesystems_size_d_datetime_hostname_mount_point ON mv_metric_filesystems_size_d(datetime, hostname, mount_point);


CREATE MATERIALIZED VIEW mv_metric_temp_files_size_tblspc_h(datetime, hostname, port, spcname, size, w) AS SELECT date_trunc('hour', datetime), hostname, port, spcname, (SUM(size)/COUNT(*))::BIGINT AS size, COUNT(*) AS w FROM metric_temp_files_size_tblspc GROUP BY date_trunc('hour', datetime), hostname, port, spcname;

CREATE UNIQUE INDEX i_mv_metric_temp_files_size_tblspc_h_datetime_hostname_port_spcname ON mv_metric_temp_files_size_tblspc_h(datetime, hostname, port, spcname);

CREATE MATERIALIZED VIEW mv_metric_temp_files_size_tblspc_d(datetime, hostname, port, spcname, size, w) AS SELECT date_trunc('day', datetime), hostname, port, spcname, (SUM(size)/SUM(w))::BIGINT AS size, SUM(w) AS w FROM (SELECT datetime, hostname, port, spcname, size*w AS size, w FROM mv_metric_temp_files_size_tblspc_h) AS sq1 GROUP BY date_trunc('day', datetime), hostname, port, spcname;

CREATE UNIQUE INDEX i_mv_metric_temp_files_size_tblspc_d_datetime_hostname_port_spcname ON mv_metric_temp_files_size_tblspc_d(datetime, hostname, port, spcname);

CREATE MATERIALIZED VIEW mv_metric_temp_files_size_db_h(datetime, hostname, port, dbname, size, w) AS SELECT date_trunc('hour', datetime), hostname, port, dbname, (SUM(size)/COUNT(*))::BIGINT AS size, COUNT(*) AS w FROM metric_temp_files_size_db GROUP BY date_trunc('hour', datetime), hostname, port, dbname;

CREATE UNIQUE INDEX i_mv_metric_temp_files_size_db_h_datetime_hostname_port_dbname ON mv_metric_temp_files_size_db_h(datetime, hostname, port, dbname);

CREATE MATERIALIZED VIEW mv_metric_temp_files_size_db_d(datetime, hostname, port, dbname, size, w) AS SELECT date_trunc('day', datetime), hostname, port, dbname, (SUM(size)/SUM(w))::BIGINT AS size, SUM(w) AS w FROM (SELECT datetime, hostname, port, dbname, size*w AS size, w FROM mv_metric_temp_files_size_db_h) AS sq1 GROUP BY date_trunc('day', datetime), hostname, port, dbname;

CREATE UNIQUE INDEX i_mv_metric_temp_files_size_db_d_datetime_hostname_port_dbname ON mv_metric_temp_files_size_db_d(datetime, hostname, port, dbname);


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

CREATE MATERIALIZED VIEW mv_metric_wal_files_h(datetime, hostname, port, measure_interval, written_size, total, archive_ready, total_size, current_location) AS SELECT date_trunc('hour', datetime), hostname, port, SUM(measure_interval) AS measure_interval, SUM(written_size) AS written_size, SUM(total) AS total, SUM(archive_ready) AS archive_ready, SUM(total_size) AS total_size, MIN(current_location::pg_lsn)::TEXT AS current_location  FROM metric_wal_files GROUP BY date_trunc('hour', datetime), hostname, port;

CREATE UNIQUE INDEX i_mv_metric_wal_files_h_datetime_hostname_port ON mv_metric_wal_files_h(datetime, hostname, port);

CREATE MATERIALIZED VIEW mv_metric_wal_files_d(datetime, hostname, port, measure_interval, written_size, total, archive_ready, total_size, current_location) AS SELECT date_trunc('day', datetime), hostname, port, SUM(measure_interval) AS measure_interval, SUM(written_size) AS written_size, SUM(total) AS total, SUM(archive_ready) AS archive_ready, SUM(total_size) AS total_size, MIN(current_location::pg_lsn)::TEXT AS current_location  FROM mv_metric_wal_files_h GROUP BY date_trunc('day', datetime), hostname, port;

CREATE UNIQUE INDEX i_mv_metric_wal_files_d_datetime_hostname_port ON mv_metric_wal_files_d(datetime, hostname, port);


CREATE MATERIALIZED VIEW mv_metric_cpu_h(datetime, hostname, cpu, measure_interval, time_user, time_system, time_idle, time_iowait, time_steal) AS SELECT date_trunc('hour', datetime), hostname, cpu, SUM(measure_interval) AS measure_interval, SUM(time_user) AS time_user, SUM(time_system) AS time_system, SUM(time_idle) AS time_idle, SUM(time_iowait) AS time_iowait, SUM(time_steal) AS time_steal FROM metric_cpu GROUP BY date_trunc('hour', datetime), hostname, cpu;

CREATE UNIQUE INDEX i_mv_metric_cpu_h_datetime_hostname_cpu ON mv_metric_cpu_h(datetime, hostname, cpu);

CREATE MATERIALIZED VIEW mv_metric_cpu_d(datetime, hostname, cpu, measure_interval, time_user, time_system, time_idle, time_iowait, time_steal) AS SELECT date_trunc('day', datetime), hostname, cpu, SUM(measure_interval) AS measure_interval, SUM(time_user) AS time_user, SUM(time_system) AS time_system, SUM(time_idle) AS time_idle, SUM(time_iowait) AS time_iowait, SUM(time_steal) AS time_steal FROM mv_metric_cpu_h GROUP BY date_trunc('day', datetime), hostname, cpu;

CREATE UNIQUE INDEX i_mv_metric_cpu_d_datetime_hostname_cpu ON mv_metric_cpu_d(datetime, hostname, cpu);

CREATE MATERIALIZED VIEW mv_metric_process_h (datetime, hostname, measure_interval, context_switches, forks, procs_running, procs_blocked, procs_total, w) AS SELECT date_trunc('hour', datetime) AS datetime, hostname, SUM(measure_interval) AS measure_interval, SUM(context_switches) AS context_switches, SUM(forks) AS forks, (SUM(procs_running)/COUNT(*))::INT AS procs_running, (SUM(procs_blocked)/COUNT(*))::INT AS procs_blocked, (SUM(procs_total)/COUNT(*))::INT AS procs_total, COUNT(*) AS w FROM metric_process GROUP BY date_trunc('hour', datetime), hostname;

CREATE UNIQUE INDEX i_mv_metric_process_h_datetime_hostname ON mv_metric_process_h(datetime, hostname);

CREATE MATERIALIZED VIEW mv_metric_process_d (datetime, hostname, measure_interval, context_switches, forks, procs_running, procs_blocked, procs_total, w) AS SELECT date_trunc('day', datetime) AS datetime, hostname, SUM(measure_interval) AS measure_interval, SUM(context_switches) AS context_switches, SUM(forks) AS forks, (SUM(procs_running)/SUM(w))::INT AS procs_running, (SUM(procs_blocked)/SUM(w))::INT AS procs_blocked, (SUM(procs_total)/SUM(w))::INT AS procs_total, SUM(w) AS w FROM (SELECT datetime, hostname, measure_interval, context_switches, forks, procs_running*w AS procs_running, procs_blocked*w AS procs_blocked, procs_total*w AS procs_total, w FROM mv_metric_process_h) AS sq1 GROUP BY date_trunc('day', datetime), hostname;

CREATE UNIQUE INDEX i_mv_metric_process_d_datetime_hostname ON mv_metric_process_d(datetime, hostname);

CREATE MATERIALIZED VIEW mv_metric_memory_h (datetime, hostname, mem_total, mem_used, mem_free, mem_buffers, mem_cached, swap_total, swap_used, w) AS SELECT date_trunc('hour', datetime) AS datetime, hostname, (SUM(mem_total)/COUNT(*))::BIGINT AS mem_total, (SUM(mem_used)/COUNT(*))::BIGINT AS mem_used, (SUM(mem_free)/COUNT(*))::BIGINT AS mem_free, (SUM(mem_buffers)/COUNT(*))::BIGINT AS mem_buffers, (SUM(mem_cached)/COUNT(*))::BIGINT AS mem_cached, (SUM(swap_total)/COUNT(*))::BIGINT AS swap_total, (SUM(swap_used)/COUNT(*))::BIGINT AS swap_used, COUNT(*) AS w FROM metric_memory GROUP BY date_trunc('hour', datetime), hostname;

CREATE UNIQUE INDEX i_mv_metric_memory_h_datetime_hostname ON mv_metric_memory_h(datetime, hostname);

CREATE MATERIALIZED VIEW mv_metric_memory_d (datetime, hostname, mem_total, mem_used, mem_free, mem_buffers, mem_cached, swap_total, swap_used, w) AS SELECT date_trunc('day', datetime) AS datetime, hostname, (SUM(mem_total)/SUM(w))::BIGINT AS mem_total, (SUM(mem_used)/SUM(w))::BIGINT AS mem_used, (SUM(mem_free)/SUM(w))::BIGINT AS mem_free, (SUM(mem_buffers)/SUM(w))::BIGINT AS mem_buffers, (SUM(mem_cached)/SUM(w))::BIGINT AS mem_cached, (SUM(swap_total)/SUM(w))::BIGINT AS swap_total, (SUM(swap_used)/SUM(w))::BIGINT AS swap_used, SUM(w) AS w FROM (SELECT datetime, hostname, mem_total*w AS mem_total, mem_used*w AS mem_used, mem_free*w AS mem_free, mem_buffers*w AS mem_buffers, mem_cached*w AS mem_cached, swap_total*w AS swap_total, swap_used*w AS swap_used, w FROM mv_metric_memory_h) AS sq1 GROUP BY date_trunc('day', datetime), hostname;

CREATE UNIQUE INDEX i_mv_metric_memory_d_datetime_hostname ON mv_metric_memory_d(datetime, hostname);
 
CREATE MATERIALIZED VIEW mv_metric_vacuum_analyze_h (datetime, hostname, port, dbname, measure_interval, n_vacuum, n_analyze, n_autovacuum, n_autoanalyze) AS SELECT date_trunc('hour', datetime) AS datetime, hostname, port, dbname, SUM(measure_interval) AS measure_interval, SUM(n_vacuum) AS n_vacuum, SUM(n_analyze) AS n_analyze, SUM(n_autovacuum) AS n_autovacuum, SUM(n_autoanalyze) AS n_autoanalyze FROM metric_vacuum_analyze GROUP BY date_trunc('hour', datetime), hostname, port, dbname;

CREATE UNIQUE INDEX i_mv_metric_vacuum_analyze_h ON mv_metric_vacuum_analyze_h(datetime, hostname, port, dbname);

CREATE MATERIALIZED VIEW mv_metric_vacuum_analyze_d (datetime, hostname, port, dbname, measure_interval, n_vacuum, n_analyze, n_autovacuum, n_autoanalyze) AS SELECT date_trunc('day', datetime) AS datetime, hostname, port, dbname, SUM(measure_interval) AS measure_interval, SUM(n_vacuum) AS n_vacuum, SUM(n_analyze) AS n_analyze, SUM(n_autovacuum) AS n_autovacuum, SUM(n_autoanalyze) AS n_autoanalyze FROM mv_metric_vacuum_analyze_h GROUP BY date_trunc('day', datetime), hostname, port, dbname;

CREATE UNIQUE INDEX i_mv_metric_vacuum_analyze_d ON mv_metric_vacuum_analyze_d(datetime, hostname, port, dbname);

CREATE OR REPLACE FUNCTION refresh_all_matviews() RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$

DECLARE
	v_relname TEXT;
BEGIN
	FOR v_relname IN SELECT relname FROM pg_class WHERE relname LIKE 'mv\_metric\_%\_h' AND relkind = 'm' LOOP
		RAISE NOTICE 'Refreshing MV: %', v_relname;
		EXECUTE 'REFRESH MATERIALIZED VIEW CONCURRENTLY '||v_relname;
	END LOOP;
	FOR v_relname IN SELECT relname FROM pg_class WHERE relname LIKE 'mv\_metric\_%\_d' AND relkind = 'm' LOOP
		RAISE NOTICE 'Refreshing MV: %', v_relname;
		EXECUTE 'REFRESH MATERIALIZED VIEW CONCURRENTLY '||v_relname;
	END LOOP;
	RETURN true;
END;

$$;
