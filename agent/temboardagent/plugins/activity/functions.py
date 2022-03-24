from .process import Process, memory_total_size
import time
from resource import getpagesize
from temboardagent.notification import NotificationMgmt, Notification
from temboardagent.tools import validate_parameters
from temboardagent.types import T_PID
from temboardagent.errors import NotificationError


def get_activity(conn):
    """
    Returns PostgreSQL backend list based on pg_stat_activity view.
    For each backend (process) we need to compute: CPU and mem. usage, I/O
    infos.
    """
    mem_total = memory_total_size()
    page_size = getpagesize()
    if conn.server_version >= 90600 and conn.server_version < 100000:
        query = """
SELECT
  pg_stat_activity.pid AS pid,
  pg_stat_activity.datname AS database,
  pg_stat_activity.client_addr AS client,
  round(EXTRACT(epoch FROM (NOW()
    - pg_stat_activity.query_start))::numeric, 2)::FLOAT AS duration,
  CASE WHEN pg_stat_activity.wait_event_type IS
    DISTINCT FROM 'Lock' THEN 'N' ELSE 'Y' END AS wait,
  pg_stat_activity.usename AS user,
  pg_stat_activity.state AS state,
  pg_stat_activity.query AS query
FROM
  pg_stat_activity
WHERE
  pid <> pg_backend_pid()
ORDER BY
  EXTRACT(epoch FROM (NOW() - pg_stat_activity.query_start)) DESC
        """
    elif conn.server_version < 90600:
        query = """
SELECT
  pg_stat_activity.pid AS pid,
  pg_stat_activity.datname AS database,
  pg_stat_activity.client_addr AS client,
  round(EXTRACT(epoch FROM (NOW()
    - pg_stat_activity.query_start))::numeric, 2)::FLOAT AS duration,
  CASE WHEN pg_stat_activity.waiting = 't' THEN 'Y' ELSE 'N' END AS wait,
  pg_stat_activity.usename AS user,
  pg_stat_activity.state AS state,
  pg_stat_activity.query AS query
FROM
  pg_stat_activity
WHERE
  pid <> pg_backend_pid()
ORDER BY
  EXTRACT(epoch FROM (NOW() - pg_stat_activity.query_start)) DESC
        """
    elif conn.server_version >= 100000:
        query = """
SELECT
  pg_stat_activity.pid AS pid,
  pg_stat_activity.datname AS database,
  pg_stat_activity.client_addr AS client,
  round(EXTRACT(epoch FROM (NOW()
    - pg_stat_activity.query_start))::numeric, 2)::FLOAT AS duration,
  CASE WHEN pg_stat_activity.wait_event_type IS
    DISTINCT FROM 'Lock' THEN 'N' ELSE 'Y' END AS wait,
  pg_stat_activity.usename AS user,
  pg_stat_activity.state AS state,
  pg_stat_activity.query AS query
FROM
  pg_stat_activity
WHERE
  pid <> pg_backend_pid()
  AND backend_type = 'client backend'
ORDER BY
  EXTRACT(epoch FROM (NOW() - pg_stat_activity.query_start)) DESC
        """

    backend_list = []
    for row in conn.query(query):
        try:
            backend_list.append({
                'pid': row['pid'],
                'database': row['database'],
                'client': row['client'],
                'duration': row['duration'],
                'wait': row['wait'],
                'user': row['user'],
                'state': row['state'],
                'query': row['query'],
                'process': Process(row['pid'], mem_total, page_size)})
        except Exception:
            pass

    time.sleep(0.1)
    final_backend_list = []
    for row in backend_list:
        try:
            (read_s, write_s) = row['process'].io_usage()
            if row['duration'] < 0:
                row['duration'] = 0
            final_backend_list.append({
                'pid': row['pid'],
                'database': row['database'],
                'client': row['client'],
                'duration': row['duration'],
                'wait': row['wait'],
                'user': row['user'],
                'state': row['state'],
                'query': row['query'],
                'iow': row['process'].iow,
                'read_s': read_s,
                'write_s': write_s,
                'cpu': row['process'].cpu_usage(),
                'memory': row['process'].mem_usage()
            })
        except Exception:
            pass
    return {'rows': final_backend_list}


def post_activity_kill(conn, config, http_context):
    """
    Kill (using pg_terminate_backend()) processes based on a given backend PID
    list.
    """
    validate_parameters(http_context['post'], [
        ('pids', T_PID, True)
    ])
    ret = {'backends': []}
    for pid in http_context['post']['pids']:
        killed = conn.query_scalar(
            "SELECT pg_terminate_backend(%s) AS killed" % (pid))
        # Push a notification.
        try:
            NotificationMgmt.push(
                config,
                Notification(
                    username=http_context['username'],
                    message="Backend %s terminated" % (pid)
                )
            )
        except (NotificationError, Exception):
            pass

        ret['backends'].append({
            'pid': pid,
            'killed': killed,
        })
    return ret


def get_activity_waiting(conn):
    """
    Returns the list of waiting (on lock) queries.
    """
    mem_total = memory_total_size()
    page_size = getpagesize()

    query = """
SELECT
  pg_locks.pid AS pid,
  pg_stat_activity.datname AS database,
  pg_stat_activity.usename AS user,
  pg_locks.mode AS mode,
  pg_locks.locktype AS type,
  COALESCE(pg_locks.relation::regclass::text, ' ') AS relation,
  round(EXTRACT(epoch FROM (NOW()
    - pg_stat_activity.query_start))::numeric,2)::FLOAT AS duration,
  pg_stat_activity.state AS state,
  pg_stat_activity.query AS query
FROM
  pg_catalog.pg_locks JOIN pg_catalog.pg_stat_activity
    ON (pg_catalog.pg_locks.pid = pg_catalog.pg_stat_activity.pid)
WHERE
  NOT pg_catalog.pg_locks.granted
  AND pg_catalog.pg_stat_activity.pid <> pg_backend_pid()
ORDER BY
  EXTRACT(epoch FROM (NOW() - pg_stat_activity.query_start)) DESC
    """
    backend_list = []
    for row in conn.query(query):
        try:
            backend_list.append({
                'pid': row['pid'],
                'database': row['database'],
                'user': row['user'],
                'mode': row['mode'],
                'type': row['type'],
                'relation': row['relation'],
                'duration': row['duration'],
                'state': row['state'],
                'query': row['query'],
                'process': Process(row['pid'], mem_total, page_size)})
        except Exception:
            pass

    time.sleep(0.1)
    final_backend_list = []
    for row in backend_list:
        try:
            (read_s, write_s) = row['process'].io_usage()
            if row['duration'] < 0:
                row['duration'] = 0
            final_backend_list.append({
                'pid': row['pid'],
                'database': row['database'],
                'user': row['user'],
                'mode': row['mode'],
                'type': row['type'],
                'relation': row['relation'],
                'duration': row['duration'],
                'state': row['state'],
                'query': row['query'],
                'iow': row['process'].iow,
                'read_s': read_s,
                'write_s': write_s,
                'cpu': row['process'].cpu_usage(),
                'memory': row['process'].mem_usage()
            })
        except Exception:
            pass
    return {'rows': final_backend_list}


def get_activity_blocking(conn):
    """
    Returns the list of blocking (lock) queries.
    """
    mem_total = memory_total_size()
    page_size = getpagesize()

    query = """
SELECT
  pid,
  datname AS database,
  usename AS user,
  COALESCE(relation::text, ' ') AS relation,
  mode,
  locktype AS type,
  duration,
  state,
  query
FROM (
  SELECT
    blocking.pid,
    pg_stat_activity.query,
    blocking.mode,
    pg_stat_activity.datname,
    pg_stat_activity.usename,
    blocking.locktype,
    round(EXTRACT(epoch FROM (NOW()
      - pg_stat_activity.query_start))::numeric,2)::FLOAT AS duration,
    blocking.relation::regclass AS relation,
    pg_stat_activity.state AS state
  FROM
    pg_locks AS blocking
    JOIN (SELECT transactionid FROM pg_locks WHERE NOT granted) AS blocked
      ON (blocking.transactionid = blocked.transactionid)
    JOIN pg_stat_activity
      ON (blocking.pid = pg_stat_activity.pid)
  WHERE
    blocking.granted
  UNION ALL
  SELECT
    blocking.pid,
    pg_stat_activity.query,
    blocking.mode,
    pg_stat_activity.datname,
    pg_stat_activity.usename,
    blocking.locktype,
    round(EXTRACT(epoch FROM (NOW()
      - pg_stat_activity.query_start))::numeric,2)::FLOAT AS duration,
    blocking.relation::regclass AS relation,
    pg_stat_activity.state AS state
  FROM
    pg_locks AS blocking
    JOIN (SELECT database, relation, mode FROM pg_locks WHERE NOT granted
        AND relation IS NOT NULL) AS blocked
      ON (blocking.database = blocked.database
        AND blocking.relation = blocked.relation)
    JOIN pg_stat_activity
      ON (blocking.pid = pg_stat_activity.pid)
  WHERE
    blocking.granted
) AS sq
GROUP BY pid, query, mode, locktype, duration, datname, usename, relation,
  state
ORDER BY duration DESC
    """
    backend_list = []
    for row in conn.query(query):
        try:
            backend_list.append({
                'pid': row['pid'],
                'database': row['database'],
                'user': row['user'],
                'mode': row['mode'],
                'type': row['type'],
                'relation': row['relation'],
                'duration': row['duration'],
                'state': row['state'],
                'query': row['query'],
                'process': Process(row['pid'], mem_total, page_size)})
        except Exception:
            pass

    time.sleep(0.1)
    final_backend_list = []
    for row in backend_list:
        try:
            (read_s, write_s) = row['process'].io_usage()
            if row['duration'] < 0:
                row['duration'] = 0
            final_backend_list.append({
                'pid': row['pid'],
                'database': row['database'],
                'user': row['user'],
                'mode': row['mode'],
                'type': row['type'],
                'relation': row['relation'],
                'duration': row['duration'],
                'state': row['state'],
                'query': row['query'],
                'iow': row['process'].iow,
                'read_s': read_s,
                'write_s': write_s,
                'cpu': row['process'].cpu_usage(),
                'memory': row['process'].mem_usage()
            })
        except Exception:
            pass
    return {'rows': final_backend_list}
