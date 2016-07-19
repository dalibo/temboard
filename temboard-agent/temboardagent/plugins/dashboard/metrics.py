import time
from os import getloadavg
import re
import json

from temboardagent.queue import Queue, Message
from temboardagent.command import exec_command
from temboardagent.notification import NotificationMgmt, Notification
from temboardagent.errors import NotificationError

def get_metrics(conn, config, _ = None):
    dm = DashboardMetrics(conn)
    return {'buffers': dm.get_buffers(),
            'hitratio': dm.get_hitratio(),
            'active_backends': dm.get_active_backends(),
            'cpu': dm.get_cpu_usage(),
            'loadaverage': dm.get_load_average(),
            'memory': dm.get_memory_usage(),
            'hostname': dm.get_hostname(),
            'os_version': dm.get_os_version(),
            'databases': dm.get_stat_db(),
            'pg_uptime': dm.get_pg_uptime(),
            'n_cpu': dm.get_n_cpu(),
            'pg_version': dm.get_pg_version(),
            'pg_data': dm.get_pg_data(),
            'pg_port': dm.get_pg_port(),
            'notifications': dm.get_notifications(config)}

def get_metrics_queue(config, _ = None):
    q = Queue('%s/dashboard.q'% (config.temboard['home']), max_length = (config.plugins['dashboard']['history_length']+1), overflow_mode = 'slide')
    dm = DashboardMetrics()
    msg = q.get_last_message()
    msg['notifications'] = dm.get_notifications(config)
    return msg

def get_history_metrics_queue(config, _ = None):
    q = Queue('%s/dashboard.q'% (config.temboard['home']), max_length = (config.plugins['dashboard']['history_length']+1), overflow_mode = 'slide')
    return q.get_content_all_messages()

def get_info(conn, config, _):
    dm = DashboardMetrics(conn)
    return {
            'hostname': dm.get_hostname(),
            'os_version': dm.get_os_version(),
            'pg_uptime': dm.get_pg_uptime(),
            'pg_data': dm.get_pg_data(),
            'pg_version': dm.get_pg_version(),
            'pg_port': dm.get_pg_port()
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
    dm = DashboardMetrics()
    return {'hostname': dm.get_hostname()}

def get_os_version(config, _):
    dm = DashboardMetrics()
    return {'os_version': dm.get_os_version()}

def get_databases(conn, config, _):
    dm = DashboardMetrics(conn)
    return {'databases': dm.get_stat_db()}

def get_n_cpu(config, _):
    dm = DashboardMetrics()
    return {'n_cpu': dm.get_n_cpu()}

def get_pg_version(conn, config, _):
    dm = DashboardMetrics(conn)
    return {'pg_version': dm.get_pg_version()}

def get_pg_uptime(conn, config, _):
    dm = DashboardMetrics(conn)
    return {'pg_uptime': dm.get_pg_uptime()}

def get_pg_port(conn, config, _):
    dm = DashboardMetrics(conn)
    return {'pg_port': dm.get_pg_port()}

def get_pg_data(conn, config, _):
    dm = DashboardMetrics(conn)
    return {'pg_data': dm.get_pg_data()}

class DashboardMetrics(object):
    conn = None
    config = None
    system = 'Linux'
    _instance = None
    def __init__(self, conn = None):
        self.conn = conn

    def get_buffers(self,):
        current_time = time.time()
        current_buffers = self._get_current_buffers()
        return {'nb': current_buffers,
                'time': current_time}

    def get_hitratio(self,):
        query = """SELECT CASE sum(blks_hit) WHEN 0 THEN NULL ELSE
        trunc((sum(blks_hit) - sum(blks_read)) / sum(blks_hit)*100) END
        AS hitratio FROM pg_stat_database"""
        self.conn.execute(query)
        return list(self.conn.get_rows())[0]['hitratio']

    def get_active_backends(self,):
        current_time = time.time()
        current_active_backends = self._get_current_active_backends()
        return {'nb': current_active_backends,
                'time': current_time}
 
    def get_cpu_usage(self,):
        if self.system == 'Linux':
            return self._get_cpu_usage_linux()

    def get_load_average(self,):
        return getloadavg()[0]

    def get_memory_usage(self,):
        if self.system == 'Linux':
            return self._get_memory_usage_linux()

    def get_pg_version(self,):
        query = "SELECT regexp_replace(version(), '^PostgreSQL ([^\s]+).*$', '\\1') AS num_version"
        self.conn.execute(query)
        return list(self.conn.get_rows())[0]['num_version']

    def get_stat_db(self,):
        query = """SELECT count(datid) as databases,
        pg_size_pretty(sum(pg_database_size(pg_database.datname))::bigint) as total_size,
        to_char(now(),'HH24:MI') as time, sum(xact_commit)::BIGINT as total_commit,
        sum(xact_rollback)::BIGINT as total_rollback FROM pg_database JOIN pg_stat_database ON
        (pg_database.oid = pg_stat_database.datid) WHERE datistemplate = 'f'"""
        self.conn.execute(query)
        row = list(self.conn.get_rows())[0]
        return {'databases': row['databases'],
                'total_size': row['total_size'],
                'time': row['time'],
                'total_commit': row['total_commit'],
                'total_rollback': row['total_rollback'],
                'timestamp': time.time()}

    def get_hostname(self,):
        if self.system == 'Linux':
            return self._get_hostname_linux()

    def get_os_version(self,):
        if self.system == 'Linux':
            return self._get_os_version_linux()

    def get_n_cpu(self,):
        from multiprocessing import cpu_count
        return cpu_count()

    def get_pg_uptime(self,):
        query = "SELECT NOW() - pg_postmaster_start_time() AS uptime"
        self.conn.execute(query)
        return list(self.conn.get_rows())[0]['uptime']

    def get_pg_port(self,):
        query = "SELECT setting FROM pg_settings WHERE name = 'port'"
        self.conn.execute(query)
        return list(self.conn.get_rows())[0]['setting']

    def get_pg_data(self,):
        query = "SELECT setting FROM pg_settings WHERE name = 'data_directory'"
        self.conn.execute(query)
        return list(self.conn.get_rows())[0]['setting']

    def _get_os_version_linux(self,):
        (returncode, stdout, stderrout) = exec_command(['/bin/uname', '-sri'])
        if returncode == 0:
            return stdout.replace('\n', '')

    def _get_hostname_linux(self,):
        (returncode, stdout, stderrout) = exec_command(['/bin/hostname'])
        if returncode == 0:
            return stdout.replace('\n', '')

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
        for k in ['time_user', 'time_system', 'time_idle', 'time_iowait', 'time_steal']:
            delta_time_total += cpu_time_snap_1[k] - cpu_time_snap_0[k]
            delta[k] = cpu_time_snap_1[k] - cpu_time_snap_0[k]
        return {'user': round(delta['time_user'] / delta_time_total * 100, 1),
                'system': round(delta['time_system'] / delta_time_total * 100, 1),
                'idle': round(delta['time_idle'] / delta_time_total * 100, 1),
                'iowait': round(delta['time_iowait'] / delta_time_total * 100, 1),
                'steal': round(delta['time_steal'] / delta_time_total * 100, 1)}

    def _get_current_cpu_usage_linux(self,):
        ret = {}
        with open('/proc/stat', 'r') as fd:
            for line in fd.readlines():
                cols = line.split()
                if len(cols) > 0 and cols[0] == 'cpu':
                    ret['time_user'] = float(cols[1]) + float(cols[2])
                    ret['time_system'] = float(cols[3]) + float(cols[6]) + float(cols[7])
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
            query = "SELECT COUNT(*) AS nb FROM pg_stat_activity WHERE state != 'idle'"
        else:
            query = "SELECT COUNT(*) AS nb FROM pg_stat_activity WHERE current_query != '<IDLE>'"
        self.conn.execute(query)
        return list(self.conn.get_rows())[0]['nb']

    def get_notifications(self, config):
        return list(NotificationMgmt.get_last_n(config, 15))
