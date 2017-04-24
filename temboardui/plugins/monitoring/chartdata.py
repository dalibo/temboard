import cStringIO
import pandas
import datetime


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


def get_tablename(probename, start, end):
    zoom = zoom_level(start, end)
    if zoom == 1:
        return 'metric_%s_30m_current' % (probename)
    elif zoom == 2:
        return 'metric_%s_6h_current' % (probename)
    else:
        return


def get_loadaverage(session, host_id, start, end, interval):
    """
    Loadaverage data loader for chart rendering.
    """
    # Instanciate a new string buffer needed by copy_expert()
    data_buffer = cStringIO.StringIO()
    # Get a new psycopg2 cursor from the current sqlalchemy session
    cur = session.connection().connection.cursor()
    # Change working schema to 'monitoring'
    cur.execute("SET search_path TO monitoring")
    # Get the "zoom level", depending on the time interval
    zl = zoom_level(start, end)
    if interval == 'all':
        interval = ['load1', 'load5', 'load15']
    else:
        interval = [interval]
    interval_sql = (',').join(['(record).%s' % i for i in interval])
    # Usage of COPY .. TO STDOUT WITH CSV for data extraction
    query = """
COPY (
    SELECT
        datetime AS date,
        %s
    FROM""" % (interval_sql)
    if zl == 0:
        # Look up in non-aggregated data
        query += """
        monitoring.expand_data_by_host_id(
            'metric_loadavg',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        host_id integer,
        record metric_loadavg_record))
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            host_id
        )
    else:
        tablename = get_tablename('loadavg', start, end)
        query += """
        monitoring.%s
    WHERE
        host_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    ORDER BY datetime ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            host_id,
            start,
            end
        )

    # Retreive data using copy_expert()
    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_cpu(session, host_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        round((SUM((record).time_user)/(SUM((record).time_user)+SUM((record).time_system)+SUM((record).time_idle)+SUM((record).time_iowait)+SUM((record).time_steal))::float*100)::numeric, 1) AS user,
        round((SUM((record).time_system)/(SUM((record).time_user)+SUM((record).time_system)+SUM((record).time_idle)+SUM((record).time_iowait)+SUM((record).time_steal))::float*100)::numeric, 1) AS system,
        round((SUM((record).time_iowait)/(SUM((record).time_user)+SUM((record).time_system)+SUM((record).time_idle)+SUM((record).time_iowait)+SUM((record).time_steal))::float*100)::numeric, 1) AS iowait,
        round((SUM((record).time_steal)/(SUM((record).time_user)+SUM((record).time_system)+SUM((record).time_idle)+SUM((record).time_iowait)+SUM((record).time_steal))::float*100)::numeric, 1) AS steal
    FROM"""  # noqa
    if zl == 0:
        query += """
        monitoring.expand_data_by_host_id(
            'metric_cpu',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        host_id integer,
        cpu text,
        record metric_cpu_record)
    GROUP BY datetime, host_id
    ORDER BY datetime)
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            host_id
        )
    else:
        tablename = get_tablename('cpu', start, end)
        query += """
        monitoring.%s
    WHERE
        host_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    GROUP BY datetime, host_id
    ORDER BY datetime)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            host_id,
            start,
            end
        )

    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_tps(session, instance_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        round(SUM((record).n_commit)/(extract('epoch' from MIN((record).measure_interval)))) AS commit,
        round(SUM((record).n_rollback)/(extract('epoch' from MIN((record).measure_interval)))) AS rollback
    FROM"""  # noqa
    if zl == 0:
        query += """
        monitoring.expand_data_by_instance_id(
            'metric_xacts',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        instance_id integer,
        dbname text,
        record metric_xacts_record)
    GROUP BY datetime, instance_id
    ORDER BY datetime)
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            instance_id
        )
    else:
        tablename = get_tablename('xacts', start, end)
        query += """
        monitoring.%s
    WHERE
        instance_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    GROUP BY datetime, instance_id
    ORDER BY datetime)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            instance_id,
            start,
            end
        )

    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_db_size(session, instance_id, start, end):
    data_buffer = cStringIO.StringIO()
    data_pivot = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        dbname,
        (record).size
    FROM"""
    if zl == 0:
        query += """
        monitoring.expand_data_by_instance_id(
            'metric_db_size',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        instance_id integer,
        dbname text,
        record metric_db_size_record))
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            instance_id
        )
    else:
        tablename = get_tablename('db_size', start, end)
        query += """
        monitoring.%s
    WHERE
        instance_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    ORDER BY 1,2 ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            instance_id,
            start,
            end
        )

    cur.copy_expert(query, data_buffer)
    cur.close()

    df = pandas.read_csv(cStringIO.StringIO(data_buffer.getvalue()))
    dfp = df.pivot(index='date', columns='dbname', values='size')
    dfp.to_csv(data_pivot)

    data = data_pivot.getvalue()
    data_buffer.close()
    data_pivot.close()
    return data


def get_instance_size(session, instance_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        SUM((record).size) AS size
    FROM"""
    if zl == 0:
        query += """
        monitoring.expand_data_by_instance_id(
            'metric_db_size',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        instance_id integer,
        dbname text,
        record metric_db_size_record)
    GROUP BY datetime, instance_id
    ORDER BY datetime)
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            instance_id
        )
    else:
        tablename = get_tablename('db_size', start, end)
        query += """
        monitoring.%s
    WHERE
        instance_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    GROUP BY datetime, instance_id
    ORDER BY 1,2 ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            instance_id,
            start,
            end
        )
    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_memory(session, host_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        (record).mem_free AS free,
        (record).mem_cached AS cached,
        (record).mem_buffers AS buffers,
        ((record).mem_used - (record).mem_cached - (record).mem_buffers) AS other
    FROM"""  # noqa

    if zl == 0:
        query += """
        monitoring.expand_data_by_host_id(
            'metric_memory',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        host_id integer,
        record metric_memory_record))
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            host_id
        )
    else:
        tablename = get_tablename('memory', start, end)
        query += """
        monitoring.%s
    WHERE
        host_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    ORDER BY datetime)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            host_id,
            start,
            end
        )

    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_swap(session, host_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        (record).swap_used AS used
    FROM"""

    if zl == 0:
        query += """
        monitoring.expand_data_by_host_id(
            'metric_memory',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        host_id integer,
        record metric_memory_record))
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            host_id
        )
    else:
        tablename = get_tablename('memory', start, end)
        query += """
        monitoring.%s
    WHERE
        host_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    ORDER BY datetime)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            host_id,
            start,
            end
        )

    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_sessions(session, instance_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        SUM((record).active) AS active,
        SUM((record).waiting) AS waiting,
        SUM((record).idle) AS idle,
        SUM((record).idle_in_xact) AS idle_in_xact,
        SUM((record).idle_in_xact_aborted) AS idle_in_xact_aborted,
        SUM((record).fastpath) AS fastpath,
        SUM((record).disabled) AS disabled
    FROM"""
    if zl == 0:
        query += """
        monitoring.expand_data_by_instance_id(
            'metric_sessions',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        instance_id integer,
        dbname text,
        record metric_sessions_record)
    GROUP BY datetime, instance_id
    ORDER BY datetime)
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            instance_id
        )
    else:
        tablename = get_tablename('sessions', start, end)
        query += """
        monitoring.%s
    WHERE
        instance_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    GROUP BY datetime, instance_id
    ORDER BY 1,2 ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            instance_id,
            start,
            end
        )
    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_blocks(session, instance_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        ROUND(SUM((record).blks_read)/(extract('epoch' from MIN((record).measure_interval)))) AS blks_read_s,
        ROUND(SUM((record).blks_hit)/(extract('epoch' from MIN((record).measure_interval)))) AS blks_hit_s
    FROM"""  # noqa
    if zl == 0:
        query += """
        monitoring.expand_data_by_instance_id(
            'metric_blocks',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        instance_id integer,
        dbname text,
        record metric_blocks_record)
    GROUP BY datetime, instance_id
    ORDER BY datetime)
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            instance_id
        )
    else:
        tablename = get_tablename('blocks', start, end)
        query += """
        monitoring.%s
    WHERE
        instance_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    GROUP BY datetime, instance_id
    ORDER BY 1,2 ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            instance_id,
            start,
            end
        )
    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_hitreadratio(session, instance_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        CASE
            WHEN (SUM((record).blks_hit) + SUM((record).blks_read)) > 0
                THEN ROUND((SUM((record).blks_hit)::FLOAT/(SUM((record).blks_hit) + SUM((record).blks_read)::FLOAT) * 100)::numeric, 2)
                ELSE 100 END AS hit_read_ratio
    FROM"""  # noqa
    if zl == 0:
        query += """
        monitoring.expand_data_by_instance_id(
            'metric_blocks',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        instance_id integer,
        dbname text,
        record metric_blocks_record)
    GROUP BY datetime, instance_id
    ORDER BY datetime)
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            instance_id
        )
    else:
        tablename = get_tablename('blocks', start, end)
        query += """
        monitoring.%s
    WHERE
        instance_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    GROUP BY datetime, instance_id
    ORDER BY 1,2 ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            instance_id,
            start,
            end
        )
    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_checkpoints(session, instance_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        (record).checkpoints_timed AS timed,
        (record).checkpoints_req AS req,
        ROUND(((record).checkpoint_write_time/1000)::numeric, 1) AS write_time,
        ROUND(((record).checkpoint_sync_time/1000)::numeric,1) AS sync_time
    FROM"""
    if zl == 0:
        query += """
        monitoring.expand_data_by_instance_id(
            'metric_bgwriter',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        instance_id integer,
        record metric_bgwriter_record))
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            instance_id
        )
    else:
        tablename = get_tablename('bgwriter', start, end)
        query += """
        monitoring.%s
    WHERE
        instance_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    ORDER BY 1,2 ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            instance_id,
            start,
            end
        )
    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_written_buffers(session, instance_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        (record).buffers_checkpoint AS checkpoint,
        (record).buffers_clean AS clean,
        (record).buffers_backend AS backend
    FROM"""
    if zl == 0:
        query += """
        monitoring.expand_data_by_instance_id(
            'metric_bgwriter',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
            instance_id integer,
            record metric_bgwriter_record))
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            instance_id
        )
    else:
        tablename = get_tablename('bgwriter', start, end)
        query += """
        monitoring.%s
    WHERE
        instance_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    ORDER BY 1,2 ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            instance_id,
            start,
            end
        )
    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_locks(session, instance_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
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
    FROM"""
    if zl == 0:
        query += """
        monitoring.expand_data_by_instance_id(
            'metric_locks',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
            instance_id integer,
            dbname text,
            record metric_locks_record)
    GROUP BY datetime, instance_id
    ORDER BY datetime)
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            instance_id
        )
    else:
        tablename = get_tablename('locks', start, end)
        query += """
        monitoring.%s
    WHERE
        instance_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    GROUP BY datetime, instance_id
    ORDER BY 1,2 ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            instance_id,
            start,
            end
        )
    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_waiting_locks(session, instance_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
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
    FROM"""
    if zl == 0:
        query += """
        monitoring.expand_data_by_instance_id(
            'metric_locks',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        instance_id integer,
        dbname text,
        record metric_locks_record)
    GROUP BY datetime, instance_id
    ORDER BY datetime)
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            instance_id
        )
    else:
        tablename = get_tablename('locks', start, end)
        query += """
        monitoring.%s
    WHERE
        instance_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    GROUP BY datetime, instance_id
    ORDER BY 1,2 ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            instance_id,
            start,
            end
        )
    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_fs_size(session, host_id, start, end):
    data_buffer = cStringIO.StringIO()
    data_pivot = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        mount_point,
        (record).used AS size
    FROM
"""
    if zl == 0:
        query += """
        monitoring.expand_data_by_host_id(
            'metric_filesystems_size',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        host_id integer,
        mount_point text,
        record metric_filesystems_size_record))
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            host_id
        )
    else:
        tablename = get_tablename('filesystems_size', start, end)
        query += """
        monitoring.%s
    WHERE
        host_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    ORDER BY 1,2 ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            host_id,
            start,
            end
        )

    cur.copy_expert(query, data_buffer)
    cur.close()

    df = pandas.read_csv(cStringIO.StringIO(data_buffer.getvalue()))
    dfp = df.pivot(index='date', columns='mount_point', values='size')
    dfp.to_csv(data_pivot)

    data = data_pivot.getvalue()
    data_buffer.close()
    data_pivot.close()
    return data


def get_fs_usage(session, host_id, start, end):
    data_buffer = cStringIO.StringIO()
    data_pivot = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        mount_point,
        round((((record).used::FLOAT/(record).total::FLOAT)*100)::numeric, 1) AS usage
    FROM"""  # noqa

    if zl == 0:
        query += """
        monitoring.expand_data_by_host_id(
            'metric_filesystems_size',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        host_id integer,
        mount_point text,
        record metric_filesystems_size_record))
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            host_id
        )
    else:
        tablename = get_tablename('filesystems_size', start, end)
        query += """
        monitoring.%s
    WHERE
        host_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    ORDER BY 1,2 ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            host_id,
            start,
            end
        )

    cur.copy_expert(query, data_buffer)
    cur.close()

    df = pandas.read_csv(cStringIO.StringIO(data_buffer.getvalue()))
    dfp = df.pivot(index='date', columns='mount_point', values='usage')
    dfp.to_csv(data_pivot)

    data = data_pivot.getvalue()
    data_buffer.close()
    data_pivot.close()
    return data


def get_ctxforks(session, host_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        round(SUM((record).context_switches)/(extract('epoch' from MIN((record).measure_interval)))) AS context_switches_s,
        round(SUM((record).forks)/(extract('epoch' from MIN((record).measure_interval)))) AS forks_s
    FROM"""  # noqa

    if zl == 0:
        query += """
        monitoring.expand_data_by_host_id(
            'metric_process',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        host_id integer,
        record metric_process_record)
    GROUP BY datetime
    ORDER BY datetime)
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            host_id
        )
    else:
        tablename = get_tablename('process', start, end)
        query += """
        monitoring.%s
    WHERE
        host_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    GROUP BY datetime
    ORDER BY datetime)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            host_id,
            start,
            end
        )

    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_tblspc_size(session, instance_id, start, end):
    data_buffer = cStringIO.StringIO()
    data_pivot = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        spcname,
        (record).size
    FROM"""
    if zl == 0:
        query += """
        monitoring.expand_data_by_instance_id(
            'metric_tblspc_size',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        instance_id integer,
        spcname text,
        record metric_tblspc_size_record))
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            instance_id
        )
    else:
        tablename = get_tablename('tblspc_size', start, end)
        query += """
        monitoring.%s
    WHERE
        instance_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    ORDER BY 1,2 ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            instance_id,
            start,
            end
        )

    cur.copy_expert(query, data_buffer)
    cur.close()

    df = pandas.read_csv(cStringIO.StringIO(data_buffer.getvalue()))
    dfp = df.pivot(index='date', columns='spcname', values='size')
    dfp.to_csv(data_pivot)

    data = data_pivot.getvalue()
    data_buffer.close()
    data_pivot.close()
    return data


def get_wal_files_size(session, instance_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        (record).written_size,
        (record).total_size
    FROM"""
    if zl == 0:
        query += """
        monitoring.expand_data_by_instance_id(
            'metric_wal_files',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        instance_id integer,
        record metric_wal_files_record))
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            instance_id
        )
    else:
        tablename = get_tablename('wal_files', start, end)
        query += """
        monitoring.%s
    WHERE
        instance_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    ORDER BY 1,2 ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            instance_id,
            start,
            end
        )
    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_wal_files_count(session, instance_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        (record).archive_ready,
        (record).total
    FROM"""
    if zl == 0:
        query += """
        monitoring.expand_data_by_instance_id(
            'metric_wal_files',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        instance_id integer,
        record metric_wal_files_record))
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            instance_id
        )
    else:
        tablename = get_tablename('wal_files', start, end)
        query += """
        monitoring.%s
    WHERE
        instance_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    ORDER BY 1,2 ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            instance_id,
            start,
            end
        )
    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_wal_files_rate(session, instance_id, start, end):
    data_buffer = cStringIO.StringIO()
    cur = session.connection().connection.cursor()
    cur.execute("SET search_path TO monitoring")
    zl = zoom_level(start, end)
    query = """
COPY (
    SELECT
        datetime AS date,
        round(SUM((record).written_size)/(extract('epoch' from MIN((record).measure_interval)))) AS written_size_s
    FROM"""  # noqa
    if zl == 0:
        query += """
        monitoring.expand_data_by_instance_id(
            'metric_wal_files',
            tstzrange('%s', '%s'),
            %s)
    AS (datetime timestamp with time zone,
        instance_id integer,
        record metric_wal_files_record)
    GROUP BY datetime, instance_id
    ORDER BY datetime)
TO STDOUT WITH CSV HEADER""" % (
            start,
            end,
            instance_id
        )
    else:
        tablename = get_tablename('wal_files', start, end)
        query += """
        monitoring.%s
    WHERE
        instance_id = %s
        AND datetime >= '%s'
        AND datetime <= '%s'
    GROUP BY datetime, instance_id
    ORDER BY 1,2 ASC)
TO STDOUT WITH CSV HEADER""" % (
            tablename,
            instance_id,
            start,
            end
        )
    cur.copy_expert(query, data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data
