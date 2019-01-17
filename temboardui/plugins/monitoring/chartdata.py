import cStringIO
import datetime
from psycopg2.extensions import AsIs

from .pivot import pivot_timeserie


METRICS = dict(
    blocks=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    ROUND(SUM((record).blks_read)/(extract('epoch' from MIN((record).measure_interval)))) AS blks_read_s,
    ROUND(SUM((record).blks_hit)/(extract('epoch' from MIN((record).measure_interval)))) AS blks_hit_s
FROM expand_data_by_instance_id('metric_blocks', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, dbname text, record metric_blocks_record)
GROUP BY datetime, instance_id ORDER BY datetime
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    ROUND(SUM((record).blks_read)/(extract('epoch' from MIN((record).measure_interval)))) AS blks_read_s,
    ROUND(SUM((record).blks_hit)/(extract('epoch' from MIN((record).measure_interval)))) AS blks_hit_s
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
GROUP BY datetime, instance_id ORDER BY 1,2 ASC
        """,  # noqa
        probename='blocks',
    ),
    checkpoints=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).checkpoints_timed AS timed,
    (record).checkpoints_req AS req,
    ROUND(((record).checkpoint_write_time/1000)::numeric, 1) AS write_time,
    ROUND(((record).checkpoint_sync_time/1000)::numeric,1) AS sync_time
FROM expand_data_by_instance_id('metric_bgwriter', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, record metric_bgwriter_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    (record).checkpoints_timed AS timed,
    (record).checkpoints_req AS req,
    ROUND(((record).checkpoint_write_time/1000)::numeric, 1) AS write_time,
    ROUND(((record).checkpoint_sync_time/1000)::numeric,1) AS sync_time
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY 1,2 ASC
        """,  # noqa
        probename='bgwriter',
    ),
    cpu=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    round((SUM((record).time_user)/(SUM((record).time_user)+SUM((record).time_system)+SUM((record).time_idle)+SUM((record).time_iowait)+SUM((record).time_steal))::float*100)::numeric, 1) AS user,
    round((SUM((record).time_system)/(SUM((record).time_user)+SUM((record).time_system)+SUM((record).time_idle)+SUM((record).time_iowait)+SUM((record).time_steal))::float*100)::numeric, 1) AS system,
    round((SUM((record).time_iowait)/(SUM((record).time_user)+SUM((record).time_system)+SUM((record).time_idle)+SUM((record).time_iowait)+SUM((record).time_steal))::float*100)::numeric, 1) AS iowait,
    round((SUM((record).time_steal)/(SUM((record).time_user)+SUM((record).time_system)+SUM((record).time_idle)+SUM((record).time_iowait)+SUM((record).time_steal))::float*100)::numeric, 1) AS steal
FROM expand_data_by_host_id('metric_cpu', tstzrange(%(start)s, %(end)s), %(host_id)s)
AS (datetime timestamp with time zone, host_id integer, cpu text, record metric_cpu_record)
GROUP BY datetime, host_id ORDER BY datetime
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    round((SUM((record).time_user)/(SUM((record).time_user)+SUM((record).time_system)+SUM((record).time_idle)+SUM((record).time_iowait)+SUM((record).time_steal))::float*100)::numeric, 1) AS user,
    round((SUM((record).time_system)/(SUM((record).time_user)+SUM((record).time_system)+SUM((record).time_idle)+SUM((record).time_iowait)+SUM((record).time_steal))::float*100)::numeric, 1) AS system,
    round((SUM((record).time_iowait)/(SUM((record).time_user)+SUM((record).time_system)+SUM((record).time_idle)+SUM((record).time_iowait)+SUM((record).time_steal))::float*100)::numeric, 1) AS iowait,
    round((SUM((record).time_steal)/(SUM((record).time_user)+SUM((record).time_system)+SUM((record).time_idle)+SUM((record).time_iowait)+SUM((record).time_steal))::float*100)::numeric, 1) AS steal
FROM %(tablename)s
WHERE host_id = %(host_id)s AND datetime >= %(start)s AND datetime <= %(end)s
GROUP BY datetime, host_id ORDER BY datetime
        """,  # noqa
        probename='cpu',
    ),
    cpu_core=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    round(((record).time_user/((record).time_user+(record).time_system+(record).time_idle+(record).time_iowait+(record).time_steal)::float*100)::numeric, 1) AS user,
    round(((record).time_system/((record).time_user+(record).time_system+(record).time_idle+(record).time_iowait+(record).time_steal)::float*100)::numeric, 1) AS system,
    round(((record).time_iowait/((record).time_user+(record).time_system+(record).time_idle+(record).time_iowait+(record).time_steal)::float*100)::numeric, 1) AS iowait,
    round(((record).time_steal/((record).time_user+(record).time_system+(record).time_idle+(record).time_iowait+(record).time_steal)::float*100)::numeric, 1) AS steal
FROM expand_data_by_host_id('metric_cpu', tstzrange(%(start)s, %(end)s), %(host_id)s)
AS (datetime timestamp with time zone, host_id integer, cpu text, record metric_cpu_record)
WHERE cpu = %(key)s
ORDER BY datetime
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    round(((record).time_user/((record).time_user+(record).time_system+(record).time_idle+(record).time_iowait+(record).time_steal)::float*100)::numeric, 1) AS user,
    round(((record).time_system/((record).time_user+(record).time_system+(record).time_idle+(record).time_iowait+(record).time_steal)::float*100)::numeric, 1) AS system,
    round(((record).time_iowait/((record).time_user+(record).time_system+(record).time_idle+(record).time_iowait+(record).time_steal)::float*100)::numeric, 1) AS iowait,
    round(((record).time_steal/((record).time_user+(record).time_system+(record).time_idle+(record).time_iowait+(record).time_steal)::float*100)::numeric, 1) AS steal
FROM %(tablename)s
WHERE host_id = %(host_id)s AND datetime >= %(start)s AND datetime <= %(end)s AND cpu = %(key)s
ORDER BY datetime
        """,  # noqa
        probename='cpu',
    ),
    ctxforks=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    round(SUM((record).context_switches)/(extract('epoch' from MIN((record).measure_interval)))) AS context_switches_s,
    round(SUM((record).forks)/(extract('epoch' from MIN((record).measure_interval)))) AS forks_s
FROM expand_data_by_host_id('metric_process', tstzrange(%(start)s, %(end)s), %(host_id)s)
AS (datetime timestamp with time zone, host_id integer, record metric_process_record)
GROUP BY datetime ORDER BY datetime
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    round(SUM((record).context_switches)/(extract('epoch' from MIN((record).measure_interval)))) AS context_switches_s,
    round(SUM((record).forks)/(extract('epoch' from MIN((record).measure_interval)))) AS forks_s
FROM %(tablename)s
WHERE host_id = %(host_id)s AND datetime >= %(start)s AND datetime <= %(end)s
GROUP BY datetime ORDER BY datetime
        """,  # noqa,
        probename='process',
    ),
    db_size=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    dbname,
    (record).size
FROM expand_data_by_instance_id('metric_db_size', tstzrange(%(start)s, %(end)s), %(instance_id))
AS (datetime timestamp with time zone, instance_id integer, dbname text, record metric_db_size_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    dbname,
    (record).size
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY datetime, dbname
        """,  # noqa
        probename='db_size',
        pivot=dict(
            index='date',
            key='dbname',
            value='size',
        )
    ),
    fs_size=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    mount_point,
    (record).used AS size
FROM expand_data_by_host_id('metric_filesystems_size', tstzrange(%(start)s, %(end)s), %(host_id)s)
AS (datetime timestamp with time zone, host_id integer, mount_point text, record metric_filesystems_size_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    mount_point,
    (record).used AS size
FROM %(tablename)s
WHERE host_id = %(host_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY 1,2 ASC
        """,  # noqa
        probename='filesystems_size',
        pivot=dict(
            index='date',
            key='mount_point',
            value='size',
        ),
    ),
    fs_usage=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    mount_point,
    round((((record).used::FLOAT/(record).total::FLOAT)*100)::numeric, 1) AS usage
FROM expand_data_by_host_id('metric_filesystems_size', tstzrange(%(start)s, %(end)s), %(host_id)s)
AS (datetime timestamp with time zone, host_id integer, mount_point text, record metric_filesystems_size_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    mount_point,
    round((((record).used::FLOAT/(record).total::FLOAT)*100)::numeric, 1) AS usage
FROM %(tablename)s
WHERE host_id = %(host_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY 1,2 ASC
        """,  # noqa,
        probename='filesystems_size',
        pivot=dict(
            index='date',
            key='mount_point',
            value='usage',
        ),
    ),
    fs_usage_mountpoint=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    round((((record).used::FLOAT/(record).total::FLOAT)*100)::numeric, 1) AS usage
FROM expand_data_by_host_id('metric_filesystems_size', tstzrange(%(start)s, %(end)s), %(host_id)s)
AS (datetime timestamp with time zone, host_id integer, mount_point text, record metric_filesystems_size_record)
WHERE mount_point = %(key)s
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    round((((record).used::FLOAT/(record).total::FLOAT)*100)::numeric, 1) AS usage
FROM %(tablename)s
WHERE host_id = %(host_id)s AND datetime >= %(start)s AND datetime <= %(end)s AND mount_point = %(key)s
ORDER BY 1,2 ASC
        """,  # noqa,
        probename='filesystems_size',
    ),
    hitreadratio=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    CASE WHEN (SUM((record).blks_hit) + SUM((record).blks_read)) > 0
    THEN ROUND((SUM((record).blks_hit)::FLOAT/(SUM((record).blks_hit) + SUM((record).blks_read)::FLOAT) * 100)::numeric, 2)
    ELSE 100 END AS hit_read_ratio
FROM expand_data_by_instance_id('metric_blocks', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, dbname text, record metric_blocks_record)
GROUP BY datetime, instance_id ORDER BY datetime
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    CASE WHEN (SUM((record).blks_hit) + SUM((record).blks_read)) > 0
    THEN ROUND((SUM((record).blks_hit)::FLOAT/(SUM((record).blks_hit) + SUM((record).blks_read)::FLOAT) * 100)::numeric, 2)
    ELSE 100 END AS hit_read_ratio
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
GROUP BY datetime, instance_id ORDER BY 1,2 ASC
        """,  # noqa
        probename='blocks',
    ),
    hitreadratio_db=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    CASE WHEN ((record).blks_hit + (record).blks_read) > 0
    THEN ROUND((((record).blks_hit::FLOAT/((record).blks_hit + (record).blks_read)::FLOAT) * 100)::numeric, 2)
    ELSE 100 END AS hit_read_ratio
FROM expand_data_by_instance_id('metric_blocks', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, dbname text, record metric_blocks_record)
WHERE dbname = %(key)s
ORDER BY datetime
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    CASE WHEN ((record).blks_hit + (record).blks_read) > 0
    THEN ROUND((((record).blks_hit::FLOAT/((record).blks_hit + (record).blks_read)::FLOAT) * 100)::numeric, 2)
    ELSE 100 END AS hit_read_ratio
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s AND dbname = %(key)s
ORDER BY 1,2 ASC
        """,  # noqa
        probename='blocks',
    ),
    instance_size=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    SUM((record).size) AS size
FROM expand_data_by_instance_id('metric_db_size', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, dbname text, record metric_db_size_record)
GROUP BY datetime, instance_id ORDER BY datetime
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    SUM((record).size) AS size
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
GROUP BY datetime, instance_id ORDER BY 1,2 ASC
        """,  # noqa
        probename='db_size',
    ),
    loadavg=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).load1,
    (record).load5,
    (record).load15
FROM expand_data_by_host_id( 'metric_loadavg', tstzrange(%(start)s, %(end)s), %(host_id)s)
AS (datetime timestamp with time zone, host_id integer, record metric_loadavg_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    (record).load1,
    (record).load5,
    (record).load15
FROM %(tablename)s WHERE host_id = %(host_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY datetime ASC
        """,  # noqa
        probename='loadavg',
    ),
    load1=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).load1
FROM expand_data_by_host_id( 'metric_loadavg', tstzrange(%(start)s, %(end)s), %(host_id)s)
AS (datetime timestamp with time zone, host_id integer, record metric_loadavg_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    (record).load1
FROM %(tablename)s WHERE host_id = %(host_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY datetime ASC
        """,  # noqa
        probename='loadavg',
    ),
    locks=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    SUM((record).access_share) AS access_share,
    SUM((record).row_share) AS row_share,
    SUM((record).row_exclusive) AS row_exclusive,
    SUM((record).share_update_exclusive) AS share_update_exclusive,
    SUM((record).share) AS share,
    SUM((record).share_row_exclusive) AS share_row_exclusive,
    SUM((record).exclusive) AS exclusive,
    SUM((record).access_exclusive) AS access_exclusive,
    SUM((record).siread) AS siread
FROM expand_data_by_instance_id('metric_locks', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, dbname text, record metric_locks_record)
GROUP BY datetime, instance_id ORDER BY datetime
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    SUM((record).access_share) AS access_share,
    SUM((record).row_share) AS row_share,
    SUM((record).row_exclusive) AS row_exclusive,
    SUM((record).share_update_exclusive) AS share_update_exclusive,
    SUM((record).share) AS share,
    SUM((record).share_row_exclusive) AS share_row_exclusive,
    SUM((record).exclusive) AS exclusive,
    SUM((record).access_exclusive) AS access_exclusive,
    SUM((record).siread) AS siread
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
GROUP BY datetime, instance_id ORDER BY 1,2 ASC        """,  # noqa
        probename='locks',
    ),
    memory=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).mem_free AS free,
    (record).mem_cached AS cached,
    (record).mem_buffers AS buffers,
    ((record).mem_used - (record).mem_cached - (record).mem_buffers) AS other
FROM expand_data_by_host_id('metric_memory', tstzrange(%(start)s, %(end)s), %(host_id)s)
AS (datetime timestamp with time zone, host_id integer, record metric_memory_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    (record).mem_free AS free,
    (record).mem_cached AS cached,
    (record).mem_buffers AS buffers,
    ((record).mem_used - (record).mem_cached - (record).mem_buffers) AS other
FROM %(tablename)s
WHERE host_id = %(host_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY datetime
        """,  # noqa
        probename='memory',
    ),
    memory_usage=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    round(((((record).mem_total - (record).mem_free - (record).mem_cached)::FLOAT/(record).mem_total::FLOAT)*100)::numeric, 1) AS usage
FROM expand_data_by_host_id('metric_memory', tstzrange(%(start)s, %(end)s), %(host_id)s)
AS (datetime timestamp with time zone, host_id integer, record metric_memory_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    round(((((record).mem_total - (record).mem_free - (record).mem_cached)::FLOAT/(record).mem_total::FLOAT)*100)::numeric, 1) AS usage
FROM %(tablename)s
WHERE host_id = %(host_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY datetime
        """,  # noqa
        probename='memory',
    ),
    rollback_db=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    SUM((record).n_rollback) AS rollback
FROM expand_data_by_instance_id('metric_xacts', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, dbname text, record metric_xacts_record)
WHERE dbname = %(key)s
GROUP BY datetime, instance_id ORDER BY datetime
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    SUM((record).n_rollback) AS rollback
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s AND key = %(key)s
GROUP BY datetime, instance_id ORDER BY datetime
        """,  # noqa
        probename='xacts',
    ),
    sessions=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    SUM((record).active) AS active,
    SUM((record).waiting) AS waiting,
    SUM((record).idle) AS idle,
    SUM((record).idle_in_xact) AS idle_in_xact,
    SUM((record).idle_in_xact_aborted) AS idle_in_xact_aborted,
    SUM((record).fastpath) AS fastpath,
    SUM((record).disabled) AS disabled
FROM expand_data_by_instance_id('metric_sessions', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, dbname text, record metric_sessions_record)
GROUP BY datetime, instance_id ORDER BY datetime
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    SUM((record).active) AS active,
    SUM((record).waiting) AS waiting,
    SUM((record).idle) AS idle,
    SUM((record).idle_in_xact) AS idle_in_xact,
    SUM((record).idle_in_xact_aborted) AS idle_in_xact_aborted,
    SUM((record).fastpath) AS fastpath,
    SUM((record).disabled) AS disabled
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
GROUP BY datetime, instance_id ORDER BY 1,2 ASC
        """,  # noqa,
        probename='sessions',
    ),
    sessions_usage=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    round(((SUM((record).active + (record).waiting + (record).idle + (record).idle_in_xact + (record).idle_in_xact_aborted + (record).fastpath + (record).disabled)::FLOAT/(SELECT setting FROM pg_settings WHERE name = 'max_connections')::FLOAT)*100)::numeric, 1) AS session_usage
FROM expand_data_by_instance_id('metric_sessions', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, dbname text, record metric_sessions_record)
GROUP BY datetime, instance_id ORDER BY datetime
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    round(((SUM((record).active + (record).waiting + (record).idle + (record).idle_in_xact + (record).idle_in_xact_aborted + (record).fastpath + (record).disabled)::FLOAT/(SELECT setting FROM pg_settings WHERE name = 'max_connections')::FLOAT)*100)::numeric, 1) AS session_usage
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
GROUP BY datetime, instance_id ORDER BY 1,2 ASC
        """,  # noqa,
        probename='sessions',
    ),
    swap=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).swap_used AS used
FROM expand_data_by_host_id('metric_memory', tstzrange(%(start)s, %(end)s), %(host_id)s)
AS (datetime timestamp with time zone, host_id integer, record metric_memory_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    (record).swap_used AS used
FROM %(tablename)s
WHERE host_id = %(host_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY datetime
        """,  # noqa
        probename='memory',
    ),
    swap_usage=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    round((((record).swap_used::FLOAT/(record).swap_total::FLOAT)*100)::numeric, 1) AS usage
FROM expand_data_by_host_id('metric_memory', tstzrange(%(start)s, %(end)s), %(host_id)s)
AS (datetime timestamp with time zone, host_id integer, record metric_memory_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    round((((record).swap_used::FLOAT/(record).swap_total::FLOAT)*100)::numeric, 1) AS usage
FROM %(tablename)s
WHERE host_id = %(host_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY datetime
        """,  # noqa
        probename='memory',
    ),
    tblspc_size=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    spcname,
    (record).size
FROM expand_data_by_instance_id('metric_tblspc_size', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, spcname text, record metric_tblspc_size_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    spcname,
    (record).size
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY 1,2 ASC
        """,  # noqa,
        probename='tblspc_size',
        pivot=dict(
            index='date',
            key='spcname',
            value='size',
        ),
    ),
    tps=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    round(SUM((record).n_commit)/(extract('epoch' from MIN((record).measure_interval)))) AS commit,
    round(SUM((record).n_rollback)/(extract('epoch' from MIN((record).measure_interval)))) AS rollback
FROM expand_data_by_instance_id('metric_xacts', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, dbname text, record metric_xacts_record)
GROUP BY datetime, instance_id ORDER BY datetime
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    round(SUM((record).n_commit)/(extract('epoch' from MIN((record).measure_interval)))) AS commit,
    round(SUM((record).n_rollback)/(extract('epoch' from MIN((record).measure_interval)))) AS rollback
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
GROUP BY datetime, instance_id ORDER BY datetime
        """,  # noqa
        probename='xacts',
    ),
    waiting_locks=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    SUM((record).waiting_access_share) AS access_share,
    SUM((record).waiting_row_share) AS row_share,
    SUM((record).waiting_row_exclusive) AS row_exclusive,
    SUM((record).waiting_share_update_exclusive) AS share_update_exclusive,
    SUM((record).waiting_share) AS share,
    SUM((record).waiting_share_row_exclusive) AS share_row_exclusive,
    SUM((record).waiting_exclusive) AS exclusive,
    SUM((record).waiting_access_exclusive) AS access_exclusive
FROM expand_data_by_instance_id('metric_locks', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, dbname text, record metric_locks_record)
GROUP BY datetime, instance_id ORDER BY datetime
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    SUM((record).waiting_access_share) AS access_share,
    SUM((record).waiting_row_share) AS row_share,
    SUM((record).waiting_row_exclusive) AS row_exclusive,
    SUM((record).waiting_share_update_exclusive) AS share_update_exclusive,
    SUM((record).waiting_share) AS share,
    SUM((record).waiting_share_row_exclusive) AS share_row_exclusive,
    SUM((record).waiting_exclusive) AS exclusive,
    SUM((record).waiting_access_exclusive) AS access_exclusive
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
GROUP BY datetime, instance_id ORDER BY 1,2 ASC
        """,  # noqa
        probename='locks'
    ),
    waiting_sessions_db=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).waiting
FROM expand_data_by_instance_id('metric_sessions', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, dbname text, record metric_sessions_record)
WHERE dbname = %(key)s
ORDER BY datetime
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    (record).waiting
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s AND dbname = %(key)s
ORDER BY 1,2 ASC
        """,  # noqa
        probename='sessions'
    ),
    wal_files_size=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).written_size,
    (record).total_size
FROM expand_data_by_instance_id('metric_wal_files', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, record metric_wal_files_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    (record).written_size,
    (record).total_size
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY 1,2 ASC
        """,  # noqa
        probename='wal_files',
    ),
    wal_files_archive=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).archive_ready
FROM expand_data_by_instance_id('metric_wal_files', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, record metric_wal_files_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    (record).archive_ready
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY 1,2 ASC
        """,  # noqa
        probename='wal_files',
    ),
    wal_files_count=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).archive_ready,
    (record).total
FROM expand_data_by_instance_id('metric_wal_files', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, record metric_wal_files_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    (record).archive_ready,
    (record).total
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY 1,2 ASC
        """,  # noqa
        probename='wal_files',
    ),
    wal_files_rate=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    round(SUM((record).written_size)/(extract('epoch' from MIN((record).measure_interval)))) AS written_size_s
FROM expand_data_by_instance_id('metric_wal_files', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, record metric_wal_files_record)
GROUP BY datetime, instance_id ORDER BY datetime
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    round(SUM((record).written_size)/(extract('epoch' from MIN((record).measure_interval)))) AS written_size_s
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
GROUP BY datetime, instance_id ORDER BY 1,2 ASC
        """,  # noqa
        probename='wal_files',
    ),
    wal_files_total=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).total
FROM expand_data_by_instance_id('metric_wal_files', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, record metric_wal_files_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    (record).total
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY 1,2 ASC
        """,  # noqa
        probename='wal_files',
    ),
    w_buffers=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).buffers_checkpoint AS checkpoint,
    (record).buffers_clean AS clean,
    (record).buffers_backend AS backend
FROM expand_data_by_instance_id('metric_bgwriter', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, record metric_bgwriter_record)
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    (record).buffers_checkpoint AS checkpoint,
    (record).buffers_clean AS clean,
    (record).buffers_backend AS backend
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY 1,2 ASC
        """,  # noqa
        probename='bgwriter',
    ),
    replication_lag=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).lag AS lag
FROM expand_data_by_instance_id('metric_replication_lag', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, record metric_replication_lag_record)
ORDER BY 1
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    (record).lag AS lag
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s
ORDER BY 1
        """,  # noqa
        probename='replication_lag',
    ),
    replication_connection=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).connected AS connected
FROM expand_data_by_instance_id('metric_replication_connection', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, upstream text, record metric_replication_connection_record)
WHERE upstream = %(key)s
ORDER BY 1
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    (record).connected AS connected
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s AND upstream = %(key)s
ORDER BY 1
        """,  # noqa
        probename='replication_connection',
    ),
    temp_files_size_delta=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).size
FROM expand_data_by_instance_id('metric_temp_files_size_delta', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, dbname text, record metric_temp_files_size_delta_record)
WHERE dbname = %(key)s
ORDER BY 1
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    (record).size
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s AND dbname = %(key)s
ORDER BY 1
        """,  # noqa
        probename='temp_files_size_delta',
    ),
    heap_bloat=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).ratio
FROM expand_data_by_instance_id('metric_heap_bloat', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, dbname text, record metric_bloat_ratio_record)
WHERE dbname = %(key)s
ORDER BY 1
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    (record).ratio
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s AND dbname = %(key)s
ORDER BY 1
        """,  # noqa
        probename='heap_bloat',
    ),
    btree_bloat=dict(
        sql_nozoom="""
SELECT
    datetime AS date,
    (record).ratio
FROM expand_data_by_instance_id('metric_btree_bloat', tstzrange(%(start)s, %(end)s), %(instance_id)s)
AS (datetime timestamp with time zone, instance_id integer, dbname text, record metric_bloat_ratio_record)
WHERE dbname = %(key)s
ORDER BY 1
        """,  # noqa
        sql_zoom="""
SELECT
    datetime AS date,
    dbname,
    (record).ratio
FROM %(tablename)s
WHERE instance_id = %(instance_id)s AND datetime >= %(start)s AND datetime <= %(end)s AND dbname = %(key)s
ORDER BY 1
        """,  # noqa
        probename='btree_bloat',
    ),
)


def zoom_level(start, end):
    zoom = 0
    if end:
        d = end - start
    else:
        d = datetime.datetime.utcnow() - start

    if d.days > 1 and d.days <= 31:
        zoom = 1
    elif d.days > 31 and d.days <= 365:
        zoom = 2
    elif d.days > 365:
        zoom = 2
    return zoom


def get_tablename(probename, zoom):
    if zoom == 1:
        return 'metric_%s_30m_current' % (probename)
    elif zoom == 2:
        return 'metric_%s_6h_current' % (probename)
    else:
        return


def get_metric_data_csv(session, metric_name, start, end, host_id=None,
                        instance_id=None, key=None):
    if metric_name not in METRICS:
        raise IndexError("Metric '%s' not found" % metric_name)

    metric = METRICS.get(metric_name)
    # Instanciate a new string buffer needed by copy_expert()
    data_buffer = cStringIO.StringIO()
    # Get a new psycopg2 cursor from the current sqlalchemy session
    cur = session.connection().connection.cursor()
    # Change working schema to 'monitoring'
    cur.execute("SET search_path TO monitoring")
    # Get the "zoom level", depending on the time interval
    level = zoom_level(start, end)
    # Load query template
    q_tpl = metric.get('sql_nozoom') if level == 0 else metric.get('sql_zoom')
    tablename = get_tablename(metric.get('probename'), level)
    query = cur.mogrify(q_tpl, dict(host_id=host_id, instance_id=instance_id,
                                    start=start, end=end, key=key,
                                    tablename=AsIs(tablename)))
    # Retreive data using copy_expert()
    cur.copy_expert("COPY(" + query + ") TO STDOUT WITH CSV HEADER",
                    data_buffer)
    cur.close()

    if metric.get('pivot'):
        # Apply pivot rotation
        data_pivot = cStringIO.StringIO()
        pivot_timeserie(
            data_buffer,
            index=metric.get('pivot').get('index'),
            key=metric.get('pivot').get('key'),
            value=metric.get('pivot').get('value'),
            output=data_pivot
        )

        data = data_pivot.getvalue()
        data_buffer.close()
        data_pivot.close()
    else:
        data = data_buffer.getvalue()
        data_buffer.close()
    return data


def get_unavailability_csv(session, start, end, host_id, instance_id):

    # Tell when the instance was not available
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    sql = """
        SELECT datetime FROM instance_availability
        WHERE instance_id = %(instance_id)s
        AND available = 'f'
        AND datetime >= %(start)s AND datetime <= %(end)s
    """
    query = cur.mogrify(sql, dict(instance_id=instance_id,
                                  start=start, end=end))
    data_buffer = cStringIO.StringIO()
    cur.copy_expert("COPY(" + query + ") TO STDOUT", data_buffer)
    data = data_buffer.getvalue()
    data_buffer.close()

    return data


def get_availability(session, host_id, instance_id):

    # Tell whether the instance is currently available or not
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    sql = """
        SELECT available FROM instance_availability
        WHERE instance_id = :instance_id
        ORDER BY datetime desc
        LIMIT 1
    """
    result = session.execute(sql, {'instance_id': instance_id}).fetchone()
    return bool(result[0]) if result else False
