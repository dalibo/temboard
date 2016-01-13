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

def get_tablename(probename, start, end):
    zoom = zoom_level(start, end)
    if zoom == 0:
        tablename = 'metric_%s' % (probename)
    elif zoom == 1:
        tablename = 'metric_%s_10m' % (probename)
    elif zoom == 2:
        tablename = 'metric_%s_30m' % (probename)
    else:
        tablename = 'metric_%s_4h' % (probename)
    return tablename

def get_loadaverage(session, hostname, start, end):
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('loadavg', start, end)

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, load1, load5, load15 FROM supervision.%s WHERE hostname = '%s' AND datetime >= '%s' AND datetime <= '%s' ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_cpu(session, hostname, start, end):
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('cpu', start, end)

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, round((SUM(time_user)/(SUM(time_user)+SUM(time_system)+SUM(time_idle)+SUM(time_iowait)+SUM(time_steal))::float*100)::numeric, 1) AS user, round((SUM(time_system)/(SUM(time_user)+SUM(time_system)+SUM(time_idle)+SUM(time_iowait)+SUM(time_steal))::float*100)::numeric, 1) AS system, round((SUM(time_iowait)/(SUM(time_user)+SUM(time_system)+SUM(time_idle)+SUM(time_iowait)+SUM(time_steal))::float*100)::numeric, 1) AS iowait, round((SUM(time_steal)/(SUM(time_user)+SUM(time_system)+SUM(time_idle)+SUM(time_iowait)+SUM(time_steal))::float*100)::numeric, 1) AS steal FROM supervision.%s WHERE hostname = '%s' AND datetime >= '%s' AND datetime <= '%s' GROUP BY datetime, hostname ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_tps(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('xacts', start, end)

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
    tablename = get_tablename('db_size', start, end)

    q_header = "SELECT DISTINCT(dbname) FROM supervision."+tablename+" WHERE hostname = :hostname AND port = :port AND datetime >= :start AND datetime <= :end ORDER BY dbname"
    result = session.execute(q_header, {"hostname": hostname, "start": start.strftime('%Y-%m-%dT%H:%M:%S'), "end": end.strftime('%Y-%m-%dT%H:%M:%S'), "port": port})

    for row in result.fetchall():
        col += ", COALESCE(%s,0) AS %s" % (row[0], row[0])
        col_type += ", %s BIGINT" % (row[0])

    q_copy = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS Date %s FROM crosstab('SELECT datetime, dbname, size FROM supervision.%s WHERE hostname = ''%s'' AND port = %s AND datetime >= ''%s'' AND datetime <= ''%s'' ORDER BY 1,2 ASC', 'SELECT DISTINCT(dbname) FROM supervision.%s WHERE datetime >= ''%s'' AND datetime <= ''%s'' ORDER BY dbname') AS ct(datetime timestamp with time zone %s)) TO STDOUT WITH CSV HEADER"
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
    tablename = get_tablename('db_size', start, end)

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
    tablename = get_tablename('memory', start, end)

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, mem_free AS free, mem_cached AS cached, mem_buffers AS buffers, (mem_used - mem_cached - mem_buffers) AS other  FROM supervision.%s WHERE hostname = '%s' AND datetime >= '%s' AND datetime <= '%s' ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_swap(session, hostname, start, end):
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('memory', start, end)

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, swap_used AS used FROM supervision.%s WHERE hostname = '%s' AND datetime >= '%s' AND datetime <= '%s' ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_sessions(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('sessions', start, end)

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, SUM(active) AS active, SUM(waiting) AS waiting, SUM(idle) AS idle, SUM(idle_in_xact) AS idle_in_xact, SUM(idle_in_xact_aborted) AS idle_in_xact_aborted, SUM(fastpath) AS fastpath, SUM(disabled) AS disabled FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' GROUP BY datetime, hostname, port ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_blocks(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('blocks', start, end)

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, ROUND(SUM(blks_read)/(extract('epoch' from MIN(measure_interval)))) AS blks_read_s, ROUND(SUM(blks_hit)/(extract('epoch' from MIN(measure_interval)))) AS blks_hit_s FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' GROUP BY datetime, hostname, port ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_hitreadratio(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('blocks', start, end)

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, ROUND((SUM(blks_hit)::FLOAT/(SUM(blks_hit) + SUM(blks_read)::FLOAT) * 100)::numeric, 2) AS hit_read_ratio FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' GROUP BY datetime, hostname, port ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_checkpoints(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('bgwriter', start, end)

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, checkpoints_timed AS timed, checkpoints_req AS req, ROUND((checkpoint_write_time/1000)::numeric, 1) AS write_time, ROUND((checkpoint_sync_time/1000)::numeric,1) AS sync_time FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_written_buffers(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('bgwriter', start, end)

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, buffers_checkpoint AS checkpoint, buffers_clean AS clean, buffers_backend AS backend FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_locks(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('locks', start, end)

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, SUM(access_share) AS access_share, SUM(row_share) AS row_share, SUM(row_exclusive) AS row_exclusive, SUM(share_update_exclusive) AS share_update_exclusive, SUM(share) AS share, SUM(share_row_exclusive) AS share_row_exclusive, SUM(exclusive) AS exclusive, SUM(access_exclusive) AS access_exclusive, SUM(siread) AS siread FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' GROUP BY datetime, hostname, port ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_waiting_locks(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('locks', start, end)

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, SUM(waiting_access_share) AS access_share, SUM(waiting_row_share) AS row_share, SUM(waiting_row_exclusive) AS row_exclusive, SUM(waiting_share_update_exclusive) AS share_update_exclusive, SUM(waiting_share) AS share, SUM(waiting_share_row_exclusive) AS share_row_exclusive, SUM(waiting_exclusive) AS exclusive, SUM(waiting_access_exclusive) AS access_exclusive FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' GROUP BY datetime, hostname, port ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_fs_size(session, hostname, start, end):
    col = '';
    col_type = ''
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('filesystems_size', start, end)

    q_header = "SELECT DISTINCT(mount_point) FROM supervision."+tablename+" WHERE hostname = :hostname AND datetime >= :start AND datetime <= :end ORDER BY mount_point"
    result = session.execute(q_header, {"hostname": hostname, "start": start.strftime('%Y-%m-%dT%H:%M:%S'), "end": end.strftime('%Y-%m-%dT%H:%M:%S')})

    for row in result.fetchall():
        col += ", COALESCE(\"%s\",0) AS \"%s\"" % (row[0], row[0])
        col_type += ", \"%s\" BIGINT" % (row[0])

    q_copy = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS Date %s FROM crosstab('SELECT datetime, mount_point, used FROM supervision.%s WHERE hostname = ''%s'' AND datetime >= ''%s'' AND datetime <= ''%s'' ORDER BY 1,2 ASC', 'SELECT DISTINCT(mount_point) FROM supervision.%s WHERE datetime >= ''%s'' AND datetime <= ''%s'' ORDER BY mount_point') AS ct(datetime timestamp with time zone %s)) TO STDOUT WITH CSV HEADER"
    cur = session.connection().connection.cursor()
    str_start_date = start.strftime('%Y-%m-%dT%H:%M:%S')
    str_end_date = end.strftime('%Y-%m-%dT%H:%M:%S')
    cur.copy_expert(q_copy % (col, tablename, hostname, str_start_date, str_end_date, tablename, str_start_date, str_end_date, col_type), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_fs_usage(session, hostname, start, end):
    col = '';
    col_type = ''
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('filesystems_size', start, end)

    q_header = "SELECT DISTINCT(mount_point) FROM supervision."+tablename+" WHERE hostname = :hostname AND datetime >= :start AND datetime <= :end ORDER BY mount_point"
    result = session.execute(q_header, {"hostname": hostname, "start": start.strftime('%Y-%m-%dT%H:%M:%S'), "end": end.strftime('%Y-%m-%dT%H:%M:%S')})

    for row in result.fetchall():
        col += ", COALESCE(\"%s\",0) AS \"%s\"" % (row[0], row[0])
        col_type += ", \"%s\" FLOAT" % (row[0])

    q_copy = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS Date %s FROM crosstab('SELECT datetime, mount_point, round(((used::FLOAT/total::FLOAT)*100)::numeric, 1) AS usage FROM supervision.%s WHERE hostname = ''%s'' AND datetime >= ''%s'' AND datetime <= ''%s'' ORDER BY 1,2 ASC', 'SELECT DISTINCT(mount_point) FROM supervision.%s WHERE datetime >= ''%s'' AND datetime <= ''%s'' ORDER BY mount_point') AS ct(datetime timestamp with time zone %s)) TO STDOUT WITH CSV HEADER"
    cur = session.connection().connection.cursor()
    str_start_date = start.strftime('%Y-%m-%dT%H:%M:%S')
    str_end_date = end.strftime('%Y-%m-%dT%H:%M:%S')
    cur.copy_expert(q_copy % (col, tablename, hostname, str_start_date, str_end_date, tablename, str_start_date, str_end_date, col_type), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_ctxforks(session, hostname, start, end):
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('process', start, end)

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, round(SUM(context_switches)/(extract('epoch' from MIN(measure_interval)))) AS context_switches_s, round(SUM(forks)/(extract('epoch' from MIN(measure_interval)))) AS forks_s FROM supervision.%s WHERE hostname = '%s' AND datetime >= '%s' AND datetime <= '%s' GROUP BY datetime ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_tblspc_size(session, hostname, port, start, end):
    col = '';
    col_type = ''
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('tblspc_size', start, end)

    q_header = "SELECT DISTINCT(spcname) FROM supervision."+tablename+" WHERE hostname = :hostname AND port = :port AND datetime >= :start AND datetime <= :end ORDER BY spcname"
    result = session.execute(q_header, {"hostname": hostname, "start": start.strftime('%Y-%m-%dT%H:%M:%S'), "end": end.strftime('%Y-%m-%dT%H:%M:%S'), "port": port})

    for row in result.fetchall():
        col += ", COALESCE(%s,0) AS %s" % (row[0], row[0])
        col_type += ", %s BIGINT" % (row[0])

    q_copy = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS Date %s FROM crosstab('SELECT datetime, spcname, size FROM supervision.%s WHERE hostname = ''%s'' AND port = %s AND datetime >= ''%s'' AND datetime <= ''%s'' ORDER BY 1,2 ASC', 'SELECT DISTINCT(spcname) FROM supervision.%s WHERE datetime >= ''%s'' AND datetime <= ''%s'' ORDER BY spcname') AS ct(datetime timestamp with time zone %s)) TO STDOUT WITH CSV HEADER"
    cur = session.connection().connection.cursor()
    str_start_date = start.strftime('%Y-%m-%dT%H:%M:%S')
    str_end_date = end.strftime('%Y-%m-%dT%H:%M:%S')
    cur.copy_expert(q_copy % (col, tablename, hostname, port, str_start_date, str_end_date, tablename, str_start_date, str_end_date, col_type), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_wal_files_size(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('wal_files', start, end)

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, written_size AS written_size, total_size AS total_size FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_wal_files_count(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('wal_files', start, end)

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, archive_ready AS archive_ready, total AS total FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data

def get_wal_files_rate(session, hostname, port, start, end):
    data_buffer = cStringIO.StringIO()
    tablename = get_tablename('wal_files', start, end)

    query = "COPY (SELECT to_char(datetime, 'YYYY/MM/DD HH24:MI:SS') AS date, round(written_size/60) AS written_size_s FROM supervision.%s WHERE hostname = '%s' AND port = %s AND datetime >= '%s' AND datetime <= '%s' ORDER BY datetime) TO STDOUT WITH CSV HEADER"

    cur = session.connection().connection.cursor()
    cur.copy_expert(query % (tablename, hostname, port, start.strftime('%Y-%m-%dT%H:%M:%S'), end.strftime('%Y-%m-%dT%H:%M:%S')), data_buffer)
    cur.close()
    data = data_buffer.getvalue()
    data_buffer.close()
    return data
