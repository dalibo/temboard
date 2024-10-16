WITH backends AS (
    SELECT SUM(writes) AS buffers_backend,
           SUM(fsyncs) AS buffers_backend_fsync
      FROM pg_stat_io
     WHERE backend_type = 'client backend'
)
SELECT cp.num_timed AS checkpoints_timed,
	   cp.num_requested AS checkpoints_req,
	   cp.write_time AS checkpoint_write_time,
	   cp.sync_time AS checkpoint_sync_time,
	   cp.buffers_written AS buffers_checkpoint,
	   bg.buffers_clean,
	   bg.maxwritten_clean,
	   backends.buffers_backend,
	   backends.buffers_backend_fsync,
	   bg.buffers_alloc,
	   bg.stats_reset
  FROM pg_stat_bgwriter AS bg,
       pg_stat_checkpointer AS cp,
       backends;
