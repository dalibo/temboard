-- Repository upgrade script from 0.0.1 to 1.1
-- Requires monitoring.sql has been loaded previously

BEGIN;

-- application schema migration
ALTER SCHEMA application OWNER TO postgres;

DO $$
DECLARE r record;
BEGIN
    FOR r IN SELECT schemaname, tablename FROM pg_tables
             WHERE schemaname = 'application'
    LOOP
        EXECUTE 'ALTER TABLE ' || quote_ident(r.schemaname) || '.' || quote_ident(r.tablename) || ' OWNER TO postgres';
    END LOOP;
END$$;

GRANT ALL ON ALL TABLES IN SCHEMA application TO temboard;
GRANT ALL ON ALL SEQUENCES IN SCHEMA application TO temboard;
GRANT ALL ON SCHEMA application TO temboard;


-- application data migration
INSERT INTO monitoring.hosts (hostname, os, os_version, os_flavour, cpu_count, cpu_arch, memory_size, swap_size, virtual) SELECT hostname, os, os_version, os_flavour, cpu_count, cpu_arch, memory_size, swap_size, virtual FROM supervision.hosts;
INSERT INTO monitoring.instances (host_id, port, local_name, version, version_num, data_directory, sysuser, standby) SELECT (SELECT host_id FROM monitoring.hosts WHERE hostname = supervision.instances.hostname), port, local_name, version, version_num, data_directory, sysuser, standby FROM supervision.instances;

-- monitoring data migration
INSERT INTO monitoring.metric_loadavg_current (datetime, host_id, record) SELECT datetime, (SELECT host_id FROM monitoring.hosts WHERE hostname = supervision.metric_loadavg.hostname), (NULL, load1, load5, load15)::monitoring.metric_loadavg_record FROM supervision.metric_loadavg ORDER BY datetime;
INSERT INTO monitoring.metric_bgwriter_current SELECT datetime, (SELECT instance_id FROM monitoring.instances JOIN monitoring.hosts USING (host_id) WHERE hostname = supervision.metric_bgwriter.hostname AND port = supervision.metric_bgwriter.port), (NULL, measure_interval, checkpoints_timed, checkpoints_req, checkpoint_write_time, checkpoint_sync_time, buffers_checkpoint, buffers_clean, maxwritten_clean, buffers_backend, buffers_backend_fsync, buffers_alloc, stats_reset)::monitoring.metric_bgwriter_record FROM supervision.metric_bgwriter ORDER BY datetime;
INSERT INTO monitoring.metric_sessions_current SELECT datetime, (SELECT instance_id FROM monitoring.instances JOIN monitoring.hosts USING (host_id) WHERE hostname = supervision.metric_sessions.hostname AND port = supervision.metric_sessions.port), dbname, (NULL, active, waiting, idle, idle_in_xact, idle_in_xact_aborted, fastpath, disabled, no_priv)::monitoring.metric_sessions_record FROM supervision.metric_sessions ORDER BY datetime;
INSERT INTO monitoring.metric_xacts_current SELECT datetime, (SELECT instance_id FROM monitoring.instances JOIN monitoring.hosts USING (host_id) WHERE hostname = supervision.metric_xacts.hostname AND port = supervision.metric_xacts.port), dbname, (NULL, measure_interval, n_commit, n_rollback)::monitoring.metric_xacts_record FROM supervision.metric_xacts ORDER BY datetime;
INSERT INTO monitoring.metric_locks_current SELECT datetime, (SELECT instance_id FROM monitoring.instances JOIN monitoring.hosts USING (host_id) WHERE hostname = supervision.metric_locks.hostname AND port = supervision.metric_locks.port), dbname, (NULL, access_share, row_share, row_exclusive, share_update_exclusive, share, share_row_exclusive, exclusive, access_exclusive, siread, waiting_access_share, waiting_row_share, waiting_row_exclusive, waiting_share_update_exclusive, waiting_share, waiting_share_row_exclusive, waiting_exclusive, waiting_access_exclusive)::monitoring.metric_locks_record FROM supervision.metric_locks ORDER BY datetime;
INSERT INTO monitoring.metric_blocks_current SELECT datetime, (SELECT instance_id FROM monitoring.instances JOIN monitoring.hosts USING (host_id) WHERE hostname = supervision.metric_blocks.hostname AND port = supervision.metric_blocks.port), dbname, (NULL, measure_interval, blks_read, blks_hit, hitmiss_ratio)::monitoring.metric_blocks_record FROM supervision.metric_blocks ORDER BY datetime;
INSERT INTO monitoring.metric_db_size_current SELECT datetime, (SELECT instance_id FROM monitoring.instances JOIN monitoring.hosts USING (host_id) WHERE hostname = supervision.metric_db_size.hostname AND port = supervision.metric_db_size.port), dbname, (NULL, size)::monitoring.metric_db_size_record FROM supervision.metric_db_size ORDER BY datetime;
INSERT INTO monitoring.metric_tblspc_size_current SELECT datetime, (SELECT instance_id FROM monitoring.instances JOIN monitoring.hosts USING (host_id) WHERE hostname = supervision.metric_tblspc_size.hostname AND port = supervision.metric_tblspc_size.port), spcname, (NULL, size)::monitoring.metric_tblspc_size_record FROM supervision.metric_tblspc_size ORDER BY datetime;
INSERT INTO monitoring.metric_filesystems_size_current SELECT datetime, (SELECT host_id FROM monitoring.hosts WHERE hostname = supervision.metric_filesystems_size.hostname), mount_point, (NULL, used, total, device)::monitoring.metric_filesystems_size_record FROM supervision.metric_filesystems_size ORDER BY datetime;
INSERT INTO monitoring.metric_temp_files_size_tblspc_current SELECT datetime, (SELECT instance_id FROM monitoring.instances JOIN monitoring.hosts USING (host_id) WHERE hostname = supervision.metric_temp_files_size_tblspc.hostname AND port = supervision.metric_temp_files_size_tblspc.port), spcname, (NULL, size)::monitoring.metric_temp_files_size_tblspc_record FROM supervision.metric_temp_files_size_tblspc ORDER BY datetime;
INSERT INTO monitoring.metric_temp_files_size_db_current SELECT datetime, (SELECT instance_id FROM monitoring.instances JOIN monitoring.hosts USING (host_id) WHERE hostname = supervision.metric_temp_files_size_db.hostname AND port = supervision.metric_temp_files_size_db.port), dbname, (NULL, size)::monitoring.metric_temp_files_size_db_record FROM supervision.metric_temp_files_size_db ORDER BY datetime;
INSERT INTO monitoring.metric_wal_files_current SELECT datetime, (SELECT instance_id FROM monitoring.instances JOIN monitoring.hosts USING (host_id) WHERE hostname = supervision.metric_wal_files.hostname AND port = supervision.metric_wal_files.port), (NULL, measure_interval, written_size, current_location, total, archive_ready, total_size)::monitoring.metric_wal_files_record FROM supervision.metric_wal_files ORDER BY datetime;
INSERT INTO monitoring.metric_cpu_current SELECT datetime, (SELECT host_id FROM monitoring.hosts WHERE hostname = supervision.metric_cpu.hostname), cpu, (NULL, measure_interval, time_user, time_system, time_idle, time_iowait, time_steal)::monitoring.metric_cpu_record FROM supervision.metric_cpu ORDER BY datetime;
INSERT INTO monitoring.metric_process_current SELECT datetime, (SELECT host_id FROM monitoring.hosts WHERE hostname = supervision.metric_process.hostname), (NULL, measure_interval, context_switches, forks, procs_running, procs_blocked, procs_total)::monitoring.metric_process_record FROM supervision.metric_process ORDER BY datetime;
INSERT INTO monitoring.metric_memory_current SELECT datetime, (SELECT host_id FROM monitoring.hosts WHERE hostname = supervision.metric_memory.hostname), (NULL, mem_total, mem_used, mem_free, mem_buffers, mem_cached, swap_total, swap_used)::monitoring.metric_memory_record FROM supervision.metric_memory ORDER BY datetime;

SELECT * FROM monitoring.history_tables();

COMMIT;
