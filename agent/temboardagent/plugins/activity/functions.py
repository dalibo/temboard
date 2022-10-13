import logging
import time
from resource import getpagesize

from .process import Process, memory_total_size


columns = [
    'pid',
    'database',
    'client',
    'duration',
    'wait',
    'user',
    'application_name',
    'state',
    'query',
    'iow',
    'read_s',
    'write_s',
    'cpu',
    'memory'
]
logger = logging.getLogger(__name__)


def get_activity(conn, limit):
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
  pg_stat_activity.query AS query,
  pg_stat_activity.application_name as application_name
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
  pg_stat_activity.query AS query,
  pg_stat_activity.application_name as application_name
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
  pg_stat_activity.query AS query,
  pg_stat_activity.application_name as application_name
FROM
  pg_stat_activity
WHERE
  pid <> pg_backend_pid()
  AND backend_type = 'client backend'
ORDER BY
  EXTRACT(epoch FROM (NOW() - pg_stat_activity.query_start)) DESC
        """

    query = query + " LIMIT %d" % limit
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
                'application_name': row['application_name'],
                'state': row['state'],
                'query': row['query'],
                'process': Process(row['pid'], mem_total, page_size)})
        except Exception as e:
            logger.debug("Failed to process activity row: %s", e)

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
                'application_name': row['application_name'],
                'state': row['state'],
                'query': row['query'],
                'iow': row['process'].iow,
                'read_s': read_s,
                'write_s': write_s,
                'cpu': row['process'].cpu_usage(),
                'memory': row['process'].mem_usage()
            })
        except Exception as e:
            logger.debug("Failed to process activity row: %s", e)
    return {
        'rows': final_backend_list,
        'columns': columns
    }


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
  pg_stat_activity.query AS query,
  pg_stat_activity.application_name as application_name
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
                'application_name': row['application_name'],
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
                'application_name': row['application_name'],
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
    return {
        'rows': final_backend_list,
        'columns': columns
    }


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
  query,
  application_name
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
    pg_stat_activity.state AS state,
    pg_stat_activity.application_name as application_name
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
    pg_stat_activity.state AS state,
    pg_stat_activity.application_name as application_name
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
ORDER BY duration DESC
    """
    backend_list = []
    for row in conn.query(query):
        try:
            backend_list.append({
                'pid': row['pid'],
                'database': row['database'],
                'user': row['user'],
                'application_name': row['application_name'],
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
                'application_name': row['application_name'],
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
    return {
        'rows': final_backend_list,
        'columns': columns
    }
