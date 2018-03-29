import time
from os import getloadavg
import re

from temboardagent.queue import Queue
from temboardagent.notification import NotificationMgmt
from temboardagent.inventory import SysInfo, PgInfo


def get_metrics(conn, config, _=None):
    dm = DashboardMetrics(conn)
    sysinfo = SysInfo()
    pginfo = PgInfo(conn)

    cpu_models = [cpu['model_name'] for cpu in sysinfo.cpu_info()['cpus']]
    cpu_models_counter = {}
    for elem in cpu_models:
        cpu_models_counter[elem] = cpu_models_counter.get(elem, 0) + 1

    return {'buffers': dm.get_buffers(),
            'hitratio': dm.get_hitratio(),
            'active_backends': dm.get_active_backends(),
            'max_connections': dm.get_max_connections(),
            'cpu': dm.get_cpu_usage(),
            'loadaverage': dm.get_load_average(),
            'memory': dm.get_memory_usage(),
            'hostname': sysinfo.hostname(config.temboard['hostname']),
            'os_version': sysinfo.os_release,
            'linux_distribution': sysinfo.linux_distribution(),
            'cpu_models': cpu_models_counter,
            'databases': dm.get_stat_db(),
            'pg_uptime': dm.get_pg_uptime(),
            'n_cpu': sysinfo.n_cpu(),
            'pg_version': pginfo.version()['full'],
            'pg_data': pginfo.setting('data_directory'),
            'pg_port': pginfo.setting('port'),
            'notifications': dm.get_notifications(config)}


def get_metrics_queue(config, _=None):
    q = Queue('%s/dashboard.q' % (config.temboard['home']))
    dm = DashboardMetrics()
    msg = q.get_last_message()
    msg['notifications'] = dm.get_notifications(config)
    return msg


def get_history_metrics_queue(config, _=None):
    q = Queue('%s/dashboard.q' % (config.temboard['home']))
    return q.get_content_all_messages()


def get_info(conn, config, _):
    dm = DashboardMetrics(conn)
    sysinfo = SysInfo()
    pginfo = PgInfo(conn)
    return {
            'hostname': sysinfo.hostname(config.temboard['hostname']),
            'os_version': "%s %s" % (sysinfo.os, sysinfo.os_release),
            'pg_uptime': dm.get_pg_uptime(),
            'pg_version': pginfo.version()['full'],
            'pg_data': pginfo.setting('data_directory'),
            'pg_port': pginfo.setting('port'),
    }


def get_buffers(conn, config, _):
    dm = DashboardMetrics(conn)
    return {'buffers': dm.get_buffers()}


def get_hitratio(conn, config, _):
    dm = DashboardMetrics(conn)
    return {'hitratio': dm.get_hitratio()}


def get_active_backends(conn, config, _):
    dm = DashboardMetrics(conn)
    return {'active_backends': dm.get_active_backends()}


def get_max_connections(conn, config, _):
    dm = DashboardMetrics(conn)
    return {'max_connections': dm.get_max_connections()}


def get_cpu_usage(config, _):
    dm = DashboardMetrics()
    return {'cpu': dm.get_cpu_usage()}


def get_loadaverage(config, _):
    dm = DashboardMetrics()
    return {'loadaverage': dm.get_load_average()}


def get_memory_usage(config, _):
    dm = DashboardMetrics()
    return {'memory': dm.get_memory_usage()}


def get_hostname(config, _):
    sysinfo = SysInfo()
    return {'hostname': sysinfo.hostname(config.temboard['hostname'])}


def get_os_version(config, _):
    sysinfo = SysInfo()
    return {'os_version': "%s %s" % (sysinfo.os, sysinfo.os_release)}


def get_databases(conn, config, _):
    dm = DashboardMetrics(conn)
    return {'databases': dm.get_stat_db()}


def get_n_cpu(config, _):
    sysinfo = SysInfo()
    return {'n_cpu': sysinfo.n_cpu()}


def get_pg_version(conn, config, _):
    pginfo = PgInfo(conn)
    return {'pg_version': pginfo.version()['full']}


def get_pg_uptime(conn, config, _):
    dm = DashboardMetrics(conn)
    return {'pg_uptime': dm.get_pg_uptime()}


def get_pg_port(conn, config, _):
    pginfo = PgInfo(conn)
    return {'pg_port': pginfo.setting('port')}


def get_pg_data(conn, config, _):
    pginfo = PgInfo(conn)
    return {'pg_data': pginfo.setting('data_directory')}


class DashboardMetrics(object):
    conn = None
    config = None
    _instance = None

    def __init__(self, conn=None):
        self.conn = conn

    def get_buffers(self,):
        current_time = time.time()
        current_buffers = self._get_current_buffers()
        return {'nb': current_buffers,
                'time': current_time}

    def get_hitratio(self,):
        query = """SELECT CASE sum(blks_hit+blks_read) WHEN 0 THEN NULL ELSE
        trunc(sum(blks_hit)/sum(blks_hit+blks_read)*100) END
        AS hitratio FROM pg_stat_database"""
        self.conn.execute(query)
        return list(self.conn.get_rows())[0]['hitratio']

    def get_active_backends(self,):
        current_time = time.time()
        current_active_backends = self._get_current_active_backends()
        return {'nb': current_active_backends,
                'time': current_time}

    def get_max_connections(self):
        query = """
SELECT setting FROM pg_settings WHERE name = 'max_connections'
            """
        self.conn.execute(query)
        return int(list(self.conn.get_rows())[0]['setting'])

    def get_cpu_usage(self,):
        sysinfo = SysInfo()
        if sysinfo.os == 'Linux':
            return self._get_cpu_usage_linux()

    def get_load_average(self,):
        return getloadavg()[0]

    def get_memory_usage(self,):
        sysinfo = SysInfo()
        if sysinfo.os == 'Linux':
            return self._get_memory_usage_linux()

    def get_stat_db(self,):
        query = """
SELECT
  count(datid) as databases,
  pg_size_pretty(sum(pg_database_size(
    pg_database.datname))::bigint) as total_size,
  to_char(now(),'HH24:MI') as time,
  sum(xact_commit)::BIGINT as total_commit,
  sum(xact_rollback)::BIGINT as total_rollback
FROM
  pg_database
  JOIN pg_stat_database ON (pg_database.oid = pg_stat_database.datid)
WHERE
  datistemplate = 'f'
        """
        self.conn.execute(query)
        row = list(self.conn.get_rows())[0]
        return {'databases': row['databases'],
                'total_size': row['total_size'],
                'time': row['time'],
                'total_commit': row['total_commit'],
                'total_rollback': row['total_rollback'],
                'timestamp': time.time()}

    def get_pg_uptime(self,):
        query = """
SELECT date_trunc('seconds', NOW() - pg_postmaster_start_time()) AS uptime
        """
        self.conn.execute(query)
        return list(self.conn.get_rows())[0]['uptime']

    def _get_memory_usage_linux(self,):
        mem_total = 0
        mem_cached = 0
        mem_free = 0
        mem_active = 0
        pattern_line_meminfo = re.compile('^([^:]+):\s+([0-9]+) kB$')
        with open('/proc/meminfo', 'r') as fd:
            for line in fd.readlines():
                m = pattern_line_meminfo.match(line)
                if m:
                    key = m.group(1)
                    value = m.group(2)
                    if key == "MemTotal":
                        mem_total = int(value)
                    if key == "MemFree":
                        mem_free = int(value)
                    if key == "Cached":
                        mem_cached = int(value)
        if mem_total == 0:
            raise Exception("Can't parse /proc/meminfo.")
        mem_active = mem_total - mem_free - mem_cached
        return {'total': mem_total,
                'free': round(float(mem_free) / float(mem_total) * 100, 1),
                'active': round(float(mem_active) / float(mem_total) * 100, 1),
                'cached': round(float(mem_cached) / float(mem_total) * 100, 1)}

    def _get_cpu_usage_linux(self,):
        cpu_time_snap_0 = self._get_current_cpu_usage_linux()
        time.sleep(0.1)
        cpu_time_snap_1 = self._get_current_cpu_usage_linux()
        delta_time_total = 0
        delta = {}
        for k in ['time_user', 'time_system', 'time_idle', 'time_iowait',
                  'time_steal']:
            delta_time_total += cpu_time_snap_1[k] - cpu_time_snap_0[k]
            delta[k] = cpu_time_snap_1[k] - cpu_time_snap_0[k]
        return {
                'user': round(delta['time_user'] / delta_time_total * 100, 1),
                'system': round(delta['time_system'] /
                                delta_time_total * 100, 1),
                'idle': round(delta['time_idle'] / delta_time_total * 100, 1),
                'iowait': round(delta['time_iowait'] /
                                delta_time_total * 100, 1),
                'steal': round(delta['time_steal'] / delta_time_total * 100, 1)
                }

    def _get_current_cpu_usage_linux(self,):
        ret = {}
        with open('/proc/stat', 'r') as fd:
            for line in fd.readlines():
                cols = line.split()
                if len(cols) > 0 and cols[0] == 'cpu':
                    ret['time_user'] = float(cols[1]) + float(cols[2])
                    ret['time_system'] = float(cols[3]) + float(cols[6]) + \
                        float(cols[7])
                    ret['time_idle'] = float(cols[4])
                    ret['time_iowait'] = float(cols[5])
                    ret['time_steal'] = float(cols[8])
                    break
        return ret

    def _get_current_buffers(self,):
        query = "SELECT buffers_alloc FROM pg_stat_bgwriter"
        self.conn.execute(query)
        return list(self.conn.get_rows())[0]['buffers_alloc']

    def _get_current_active_backends(self,):
        if self.conn.get_pg_version() >= 90200:
            query = """
SELECT COUNT(*) AS nb FROM pg_stat_activity WHERE state != 'idle'
            """
        else:
            query = """
SELECT COUNT(*) AS nb FROM pg_stat_activity WHERE current_query != '<IDLE>'
            """
        self.conn.execute(query)
        return list(self.conn.get_rows())[0]['nb']

    def get_notifications(self, config):
        return list(NotificationMgmt.get_last_n(config, 15))
