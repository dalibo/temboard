import json
import time
import os
import re

from . import db
from ...notification import NotificationMgmt
from ...inventory import SysInfo


def get_metrics(app, pool=None):
    res = dict()
    pool = pool or app.postgres.pool()
    discover = app.discover.ensure_latest()
    for attempt in pool.retry_connection():
        with attempt() as conn:
            dm = DashboardMetrics(conn)
            pgdiscover = discover['postgres']
            res.update(dict(
                buffers=dm.get_buffers(),
                hitratio=dm.get_hitratio(),
                active_backends=dm.get_active_backends(),
                max_connections=pgdiscover['max_connections'],
                databases=dm.get_stat_db(),
                pg_start_time=dm.get_pg_start_time(),
                pg_version=pgdiscover['version'],
                pg_data=pgdiscover['data_directory'],
                pg_port=pgdiscover['port'],
            ))

    sysdiscover = discover['system']
    dm = DashboardMetrics()
    res.update(dict(
        cpu=dm.get_cpu_usage(),
        loadaverage=dm.get_load_average(),
        memory=dm.get_memory_usage(),
        notifications=dm.get_notifications(app.config),
    ))

    sysinfo = SysInfo()

    cpu_models = [cpu['model_name'] for cpu in sysinfo.cpu_info()['cpus']]
    cpu_models_counter = {}
    for elem in cpu_models:
        cpu_models_counter[elem] = cpu_models_counter.get(elem, 0) + 1

    res.update(dict(
        hostname=sysdiscover['fqdn'],
        os_version=sysdiscover['os_version'],
        linux_distribution=sysdiscover['distribution'],
        cpu_models=cpu_models_counter,
        n_cpu=sysdiscover['cpu_count'],
        timestamp=time.time()
    ))
    return res


def get_metrics_queue(config):
    dm = DashboardMetrics()
    msg = dict()

    row = db.get_last_metric(
        config.temboard.home,
        'dashboard.db'
    )
    if row:
        msg = json.loads(row[0])

    msg['notifications'] = dm.get_notifications(config)
    return msg


def get_history_metrics_queue(config):
    return [
        json.loads(d)
        for d, in db.get_all_metrics(
            config.temboard.home,
            'dashboard.db'
        )
    ]


def get_buffers(conn):
    dm = DashboardMetrics(conn)
    return dict(buffers=dm.get_buffers())


def get_hitratio(conn):
    dm = DashboardMetrics(conn)
    return dict(hitratio=dm.get_hitratio())


def get_active_backends(conn):
    dm = DashboardMetrics(conn)
    return dict(active_backends=dm.get_active_backends())


def get_cpu_usage():
    dm = DashboardMetrics()
    return dict(cpu=dm.get_cpu_usage())


def get_loadaverage():
    dm = DashboardMetrics()
    return dict(loadaverage=dm.get_load_average())


def get_memory_usage():
    dm = DashboardMetrics()
    return dict(memory=dm.get_memory_usage())


def get_hostname(config):
    sysinfo = SysInfo()
    return dict(hostname=sysinfo.hostname(config.temboard.hostname))


def get_databases(conn):
    dm = DashboardMetrics(conn)
    return dict(databases=dm.get_stat_db())


class DashboardMetrics:
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
        return self.conn.queryscalar("""\
        SELECT CASE sum(blks_hit+blks_read)
          WHEN 0 THEN NULL
          ELSE trunc(sum(blks_hit)/sum(blks_hit+blks_read)*100)::float
        END AS hitratio
        FROM pg_stat_database
        """)

    def get_active_backends(self,):
        current_time = time.time()
        current_active_backends = self._get_current_active_backends()
        return {'nb': current_active_backends,
                'time': current_time}

    def get_cpu_usage(self,):
        sysinfo = SysInfo()
        if sysinfo.os == 'Linux':
            return self._get_cpu_usage_linux()

    def get_load_average(self,):
        return os.getloadavg()[0]

    def get_memory_usage(self,):
        sysinfo = SysInfo()
        if sysinfo.os == 'Linux':
            return self._get_memory_usage_linux()

    def get_stat_db(self,):
        row = self.conn.queryone("""\
        SELECT
            count(datid) as databases,
            pg_size_pretty(sum(pg_database_size(
                pg_database.datname))::bigint) as total_size,
            to_char(now(),'HH24:MI') as time,
            sum(xact_commit)::BIGINT as total_commit,
            sum(xact_rollback)::BIGINT as total_rollback
        FROM pg_database
        JOIN pg_stat_database ON (pg_database.oid = pg_stat_database.datid)
        WHERE datistemplate = 'f'
        """)
        return {'databases': row['databases'],
                'total_size': row['total_size'],
                'time': row['time'],
                'total_commit': row['total_commit'],
                'total_rollback': row['total_rollback'],
                'timestamp': time.time()}

    def get_pg_start_time(self):
        return self.conn.queryscalar("SELECT pg_postmaster_start_time();")

    def _get_memory_usage_linux(self,):
        mem_total = 0
        mem_cached = 0
        mem_free = 0
        mem_active = 0
        pattern_line_meminfo = re.compile(r'^([^:]+):\s+([0-9]+) kB$')
        with open('/proc/meminfo') as fd:
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
            'user': 0 if not delta_time_total else
            round(delta['time_user'] / delta_time_total * 100, 1),
            'system': 0 if not delta_time_total else
            round(delta['time_system'] / delta_time_total * 100, 1),
            'idle': 0 if not delta_time_total else
            round(delta['time_idle'] / delta_time_total * 100, 1),
            'iowait': 0 if not delta_time_total else
            round(delta['time_iowait'] / delta_time_total * 100, 1),
            'steal': 0 if not delta_time_total else
            round(delta['time_steal'] / delta_time_total * 100, 1)
        }

    def _get_current_cpu_usage_linux(self,):
        ret = {}
        with open('/proc/stat') as fd:
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
        return self.conn.queryscalar(
            "SELECT buffers_alloc FROM pg_stat_bgwriter"
        )

    def _get_current_active_backends(self,):
        if self.conn.server_version >= 90200:
            query = """
SELECT COUNT(*) AS nb FROM pg_stat_activity WHERE state != 'idle'
            """
        else:
            query = """
SELECT COUNT(*) AS nb FROM pg_stat_activity WHERE current_query != '<IDLE>'
            """
        return self.conn.queryscalar(query)

    def get_notifications(self, config):
        return list(NotificationMgmt.get_last_n(config, 15))
