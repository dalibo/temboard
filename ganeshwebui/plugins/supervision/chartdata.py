import cStringIO

def zoom_level(start, end):
    zoom = 0
    if end:
        d = end - start
    else:
        d = datetime.datetime.now() - start

    if d.days > 1 and d.days <= 7:
        zoom = 1
    elif d.days > 7 and d.days <= 31:
        zoom = 2
    elif d.days > 31 and d.days <= 365:
        zoom = 3
    elif d.days > 365:
        zoom = 3
    return zoom

def get_loadaverage(session, hostname, start, end):
    data_buffer = cStringIO.StringIO()
    zoom = zoom_level(start, end)
    if zoom == 0:
        tablename = 'metric_loadavg'
    elif zoom == 1:
        tablename = 'metric_loadavg_10m'
    elif zoom == 2:
        tablename = 'metric_loadavg_30m'
    else:
        tablename = 'metric_loadavg_4h'

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, load1, load5, load15 FROM supervision.%s WHERE hostname = '%s' AND datetime >= '%s' AND datetime <= '%s' ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_cpu(session, hostname, start, end):
    data_buffer = cStringIO.StringIO()
    zoom = zoom_level(start, end)
    if zoom == 0:
        tablename = 'metric_cpu'
    elif zoom == 1:
        tablename = 'metric_cpu_10m'
    elif zoom == 2:
        tablename = 'metric_cpu_30m'
    else:
        tablename = 'metric_cpu_4h'

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, round((SUM(time_user)/(SUM(time_user)+SUM(time_system)+SUM(time_idle)+SUM(time_iowait)+SUM(time_steal))::float*100)::numeric, 1) AS user, round((SUM(time_system)/(SUM(time_user)+SUM(time_system)+SUM(time_idle)+SUM(time_iowait)+SUM(time_steal))::float*100)::numeric, 1) AS system, round((SUM(time_iowait)/(SUM(time_user)+SUM(time_system)+SUM(time_idle)+SUM(time_iowait)+SUM(time_steal))::float*100)::numeric, 1) AS iowait, round((SUM(time_steal)/(SUM(time_user)+SUM(time_system)+SUM(time_idle)+SUM(time_iowait)+SUM(time_steal))::float*100)::numeric, 1) AS steal FROM supervision.%s WHERE hostname = '%s' AND datetime >= '%s' AND datetime <= '%s' GROUP BY datetime, hostname ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_tps(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    zoom = zoom_level(start, end)
    if zoom == 0:
        tablename = 'metric_xacts'
    elif zoom == 1:
        tablename = 'metric_xacts_10m'
    elif zoom == 2:
        tablename = 'metric_xacts_30m'
    else:
        tablename = 'metric_xacts_4h'

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, round(SUM(n_commit)/(extract('epoch' from MIN(measure_interval)))) AS commit, round(SUM(n_rollback)/(extract('epoch' from MIN(measure_interval)))) AS rollback FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' GROUP BY datetime, hostname, port ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data


def get_db_size(session, hostname, port, start, end):
    col = '';
    col_type = ''
    data_buffer = cStringIO.StringIO()
    zoom = zoom_level(start, end)
    if zoom == 0:
        tablename = 'metric_db_size'
    elif zoom == 1:
        tablename = 'metric_db_size_10m'
    elif zoom == 2:
        tablename = 'metric_db_size_30m'
    else:
        tablename = 'metric_db_size_4h'

    q_header = "SELECT DISTINCT(dbname) FROM supervision."+tablename+" WHERE hostname = :hostname AND port = :port AND datetime >= :start AND datetime <= :end ORDER BY dbname"
    result = session.execute(q_header, {"hostname": hostname, "start": start.strftime('%Y-%m-%dT%H:%M:%S'), "end": end.strftime('%Y-%m-%dT%H:%M:%S'), "port": port})

    for row in result.fetchall():
        col += ", COALESCE(%s,0) AS %s" % (row[0], row[0])
        col_type += ", %s BIGINT" % (row[0])

    q_copy = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS Date %s FROM crosstab('SELECT datetime, dbname, size FROM supervision.%s WHERE hostname = ''%s'' AND port = %s AND datetime >= ''%s'' AND datetime <= ''%s'' ORDER BY 1,2 ASC', 'SELECT DISTINCT(dbname) FROM supervision.%s WHERE datetime >= ''%s'' AND datetime <= ''%s'' ORDER BY datetime') AS ct(datetime timestamp with time zone %s)) TO STDOUT WITH CSV HEADER"
    cur = session.connection().connection.cursor()
    str_start_date = start.strftime('%Y-%m-%dT%H:%M:%S')
    str_end_date = end.strftime('%Y-%m-%dT%H:%M:%S')
    cur.copy_expert(q_copy % (col, tablename, hostname, port, str_start_date, str_end_date, tablename, str_start_date, str_end_date, col_type), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_instance_size(session, hostname, port, start, end):
    col = '';
    col_type = ''
    data_buffer = cStringIO.StringIO()
    zoom = zoom_level(start, end)
    if zoom == 0:
        tablename = 'metric_db_size'
    elif zoom == 1:
        tablename = 'metric_db_size_10m'
    elif zoom == 2:
        tablename = 'metric_db_size_30m'
    else:
        tablename = 'metric_db_size_4h'

    q_copy = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS Date, SUM(size) AS Size FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' GROUP BY datetime, hostname, port ORDER BY datetime ASC) TO STDOUT WITH CSV HEADER"
    cur = session.connection().connection.cursor()
    str_start_date = start.strftime('%Y-%m-%dT%H:%M:%S')
    str_end_date = end.strftime('%Y-%m-%dT%H:%M:%S')
    cur.copy_expert(q_copy % (tablename, hostname, port, str_start_date, str_end_date), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_memory(session, hostname, start, end):
    data_buffer = cStringIO.StringIO()
    zoom = zoom_level(start, end)
    if zoom == 0:
        tablename = 'metric_memory'
    elif zoom == 1:
        tablename = 'metric_memory_10m'
    elif zoom == 2:
        tablename = 'metric_memory_30m'
    else:
        tablename = 'metric_memory_4h'

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, mem_free AS free, mem_cached AS cached, mem_buffers AS buffers, (mem_used - mem_cached - mem_buffers) AS other  FROM supervision.%s WHERE hostname = '%s' AND datetime >= '%s' AND datetime <= '%s' ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_swap(session, hostname, start, end):
    data_buffer = cStringIO.StringIO()
    zoom = zoom_level(start, end)
    if zoom == 0:
        tablename = 'metric_memory'
    elif zoom == 1:
        tablename = 'metric_memory_10m'
    elif zoom == 2:
        tablename = 'metric_memory_30m'
    else:
        tablename = 'metric_memory_4h'

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, swap_used AS used FROM supervision.%s WHERE hostname = '%s' AND datetime >= '%s' AND datetime <= '%s' ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_sessions(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    zoom = zoom_level(start, end)
    if zoom == 0:
        tablename = 'metric_sessions'
    elif zoom == 1:
        tablename = 'metric_sessions_10m'
    elif zoom == 2:
        tablename = 'metric_sessions_30m'
    else:
        tablename = 'metric_sessions_4h'

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, SUM(active) AS active, SUM(waiting) AS waiting, SUM(idle) AS idle, SUM(idle_in_xact) AS idle_in_xact, SUM(idle_in_xact_aborted) AS idle_in_xact_aborted, SUM(fastpath) AS fastpath, SUM(disabled) AS disabled FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' GROUP BY datetime, hostname, port ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_blocks(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    zoom = zoom_level(start, end)
    if zoom == 0:
        tablename = 'metric_blocks'
    elif zoom == 1:
        tablename = 'metric_blocks_10m'
    elif zoom == 2:
        tablename = 'metric_blocks_30m'
    else:
        tablename = 'metric_blocks_4h'

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, ROUND(SUM(blks_read)/(extract('epoch' from MIN(measure_interval)))) AS blks_read_s, ROUND(SUM(blks_hit)/(extract('epoch' from MIN(measure_interval)))) AS blks_hit_s FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' GROUP BY datetime, hostname, port ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_hitreadratio(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    zoom = zoom_level(start, end)
    if zoom == 0:
        tablename = 'metric_blocks'
    elif zoom == 1:
        tablename = 'metric_blocks_10m'
    elif zoom == 2:
        tablename = 'metric_blocks_30m'
    else:
        tablename = 'metric_blocks_4h'

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, ROUND((SUM(blks_hit)::FLOAT/(SUM(blks_hit) + SUM(blks_read)::FLOAT) * 100)::numeric, 2) AS hit_read_ratio FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' GROUP BY datetime, hostname, port ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_checkpoints(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    zoom = zoom_level(start, end)
    if zoom == 0:
        tablename = 'metric_bgwriter'
    elif zoom == 1:
        tablename = 'metric_bgwriter_10m'
    elif zoom == 2:
        tablename = 'metric_bgwriter_30m'
    else:
        tablename = 'metric_bgwriter_4h'

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, checkpoints_timed AS timed, checkpoints_req AS req, ROUND((checkpoint_write_time/1000)::numeric, 1) AS write_time, ROUND((checkpoint_sync_time/1000)::numeric,1) AS sync_time FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_written_buffers(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    zoom = zoom_level(start, end)
    if zoom == 0:
        tablename = 'metric_bgwriter'
    elif zoom == 1:
        tablename = 'metric_bgwriter_10m'
    elif zoom == 2:
        tablename = 'metric_bgwriter_30m'
    else:
        tablename = 'metric_bgwriter_4h'

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, buffers_checkpoint AS checkpoint, buffers_clean AS clean, buffers_backend AS backend FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data
