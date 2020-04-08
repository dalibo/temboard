import operator


def bootstrap_checks(hostinfo):
    # Default checks with thresholds to run against monitoring data

    # Loadaverage (value)
    # Global to host
    yield (u"load1", hostinfo['n_cpu'] / float(2), hostinfo['n_cpu'])
    # CPU (percent)
    # One per CPU
    yield (u"cpu_core", 50, 80)
    # Memory usage (percent)
    # global
    yield (u"memory_usage", 50, 80)
    # Swap usage (percent)
    # Global to host
    yield (u"swap_usage", 30, 50)
    # Filesystems usage (percent)
    # One per filesystem
    yield (u"fs_usage_mountpoint", 80, 90)
    # Number of WAL files ready to be archived (value)
    # Global to postgres instance
    yield (u"wal_files_archive", 10, 20)
    # Number of WAL files (value)
    # Global to postgres instance
    yield (u"wal_files_total", 50, 100)
    # Number of transaction rollback (value)
    # One per DB
    yield (u"rollback_db", 10, 20)
    # Cache hitratio (percent)
    # One per DB
    yield (u"hitreadratio_db", 90, 80)
    # Client sessions vs max_connections (percent)
    # Global to postgres instance
    yield (u"sessions_usage", 80, 90)
    # Waiting sessions (value)
    # One per DB
    yield (u"waiting_sessions_db", 5, 10)
    # Replication lag
    # warning: 1MB, critical: 10MB
    yield (u"replication_lag", 1024 * 1024, 10 * 1024 * 1024)
    # Replication connection
    yield (u"replication_connection", 0, 0)
    # Temporary files size delta
    # warning: 1MB, critical: 10MB
    yield (u"temp_files_size_delta", 1024 * 1024, 10 * 1024 * 1024)
    # Heap bloat ratio
    yield (u"heap_bloat", 30, 50)
    # Btree bloat ratio
    yield (u"btree_bloat", 30, 50)


class PreProcess(object):

    @staticmethod
    def loadaverage(data):
        return float(data['loadavg'][0]['load1'])

    @staticmethod
    def cpu(data):
        _data = dict()
        for r in data['cpu']:
            total = 0
            idle = 0
            total += int(r['time_system'])
            total += int(r['time_steal'])
            total += int(r['time_iowait'])
            total += int(r['time_user'])
            total += int(r['time_idle'])
            idle = int(r['time_idle'])
            _data[r['cpu']] = int((total - idle) / float(total) * 100)
        return _data

    @staticmethod
    def memory(data):
        return int(
            (int(data['memory'][0]['mem_total'])
             - int(data['memory'][0]['mem_free'])
             - int(data['memory'][0]['mem_cached']))
            / float(data['memory'][0]['mem_total']) * 100
        )

    @staticmethod
    def swap(data):
        return int(
            int(data['memory'][0]['swap_used'])
            / float(data['memory'][0]['swap_total']) * 100
        )

    @staticmethod
    def fs(data):
        _data = dict()
        for r in data['filesystems_size']:
            _data[r['mount_point']] = int(int(r['used']) / float(r['total'])
                                          * 100)
        return _data

    @staticmethod
    def archive_ready(data):
        return int(data['wal_files'][0]['archive_ready'])

    @staticmethod
    def wal_files(data):
        return int(data['wal_files'][0]['total'])

    @staticmethod
    def xacts_rollback(data):
        _data = dict()
        for r in data['xacts']:
            _data[r['dbname']] = int(r['n_rollback'])
        return _data

    @staticmethod
    def hitratio(data):
        _data = dict()
        for r in data['blocks']:
            hit = int(r['blks_hit'])
            read = int(r['blks_read'])
            _data[r['dbname']] = (100 * hit / (hit + read)) \
                if read + hit > 0 else 100
        return _data

    @staticmethod
    def sessions(data):
        n = 0
        for r in data['sessions']:
            n += int(r['idle_in_xact'])
            n += int(r['idle_in_xact_aborted'])
            n += int(r['no_priv'])
            n += int(r['idle'])
            n += int(r['disabled'])
            n += int(r['waiting'])
            n += int(r['active'])
            n += int(r['fastpath'])
        return int(n / float(data['max_connections']) * 100)

    @staticmethod
    def waiting(data):
        _data = dict()
        for r in data['sessions']:
            _data[r['dbname']] = int(r['waiting'])
        return _data

    @staticmethod
    def replication_lag(data):
        return int(data['replication_lag'][0]['lag'])

    @staticmethod
    def replication_connection(data):
        k = data['replication_connection'][0]['upstream']
        v = int(data['replication_connection'][0]['connected'])
        return {k: v}

    @staticmethod
    def temp_files_size_delta(data):
        _data = dict()
        for r in data['temp_files_size_delta']:
            _data[r['dbname']] = int(r['size'])
        return _data

    @staticmethod
    def heap_bloat(data):
        _data = dict()
        for r in data['heap_bloat']:
            _data[r['dbname']] = int(r['ratio'])
        return _data

    @staticmethod
    def btree_bloat(data):
        _data = dict()
        for r in data['btree_bloat']:
            _data[r['dbname']] = int(r['ratio'])
        return _data


check_specs = dict(
    load1=dict(
        category='system',
        description='Loadaverage',
        preprocess=PreProcess.loadaverage,
        message='{value} is greater than {threshold}',
        operator=operator.gt,
    ),
    cpu_core=dict(
        category='system',
        description='CPU usage',
        preprocess=PreProcess.cpu,
        message='{value}% is greater than {threshold}%',
        operator=operator.gt,
        value_type='percent',
    ),
    memory_usage=dict(
        category='system',
        description='Memory usage',
        preprocess=PreProcess.memory,
        message='{value}% is greater than {threshold}%',
        operator=operator.gt,
        value_type='percent'
    ),
    swap_usage=dict(
        category='system',
        description='Swap usage',
        preprocess=PreProcess.swap,
        message='{value}% is greater than {threshold}%',
        operator=operator.gt,
        value_type='percent',
    ),
    fs_usage_mountpoint=dict(
        category='system',
        description='File systems usage',
        preprocess=PreProcess.fs,
        message='{key}: {value}% is greater than {threshold}%',
        operator=operator.gt,
        value_type='percent',
    ),
    wal_files_archive=dict(
        category='postgres',
        description='WAL files ready to be archived',
        preprocess=PreProcess.archive_ready,
        message='{value} is greater than {threshold}',
        operator=operator.gt,
    ),
    wal_files_total=dict(
        category='postgres',
        description='WAL files',
        preprocess=PreProcess.wal_files,
        message='{value} is greater than {threshold}',
        operator=operator.gt,
    ),
    rollback_db=dict(
        category='postgres',
        description='Rollbacked transactions',
        preprocess=PreProcess.xacts_rollback,
        message='{key}: {value} is greater than {threshold}',
        operator=operator.gt,
    ),
    hitreadratio_db=dict(
        category='postgres',
        description='Cache Hit Ratio',
        preprocess=PreProcess.hitratio,
        message='{key}: {value} is less than {threshold}',
        operator=operator.lt,
        value_type='percent',
    ),
    sessions_usage=dict(
        category='postgres',
        description='Client sessions',
        preprocess=PreProcess.sessions,
        message='{value} is greater than {threshold}',
        operator=operator.gt,
        value_type='percent',
    ),
    waiting_sessions_db=dict(
        category='postgres',
        description='Waiting sessions',
        preprocess=PreProcess.waiting,
        message='{key}: {value} is greater than {threshold}',
        operator=operator.gt,
    ),
    replication_lag=dict(
        category='postgres',
        description='Streaming replication lag',
        preprocess=PreProcess.replication_lag,
        message='{key}: {value} is greater than {threshold}',
        operator=operator.gt,
    ),
    replication_connection=dict(
        category='postgres',
        description='Streaming replication connection',
        preprocess=PreProcess.replication_connection,
        message='{key}: not connected',
        operator=operator.eq,
    ),
    temp_files_size_delta=dict(
        category='postgres',
        description='Temporary files size (delta)',
        preprocess=PreProcess.temp_files_size_delta,
        message='{key}: {value} is greater than {threshold}',
        operator=operator.gt,
    ),
    heap_bloat=dict(
        category='postgres',
        description='Heap bloat ratio estimation',
        preprocess=PreProcess.heap_bloat,
        message='{key}: {value} is greater than {threshold}',
        operator=operator.gt,
    ),
    btree_bloat=dict(
        category='postgres',
        description='BTree index bloat ratio estimation',
        preprocess=PreProcess.btree_bloat,
        message='{key}: {value} is greater than {threshold}',
        operator=operator.gt,
    ),
)


def get_highest_state(states):
    """
    Returns the highest state.
    """
    levels = ['UNDEF', 'OK', 'WARNING', 'CRITICAL']
    return levels[max([levels.index(state) for state in states])]


def checks_info(session, host_id, instance_id):
    """
    Returns alerting checks with current state by host_id/instance_id
    """
    query = """
SELECT c.name, c.warning, c.critical, c.description, c.enabled,
json_agg(json_build_object('key', cs.key, 'state', cs.state)) AS state_by_key
FROM monitoring.checks c JOIN monitoring.check_states cs ON (c.check_id = cs.check_id)
WHERE host_id = :host_id AND instance_id = :instance_id
GROUP BY 1,2,3,4,5 ORDER BY 1
    """  # noqa
    res = session.execute(query,
                          dict(host_id=host_id, instance_id=instance_id))
    ret = []
    for row in res.fetchall():
        c_row = dict(row)
        c_row['state'] = get_highest_state([o['state']
                                            for o in c_row['state_by_key']])
        ret.append(c_row)
    return ret


def check_state_detail(session, host_id, instance_id, check_name):
    query = """
SELECT json_agg(json_build_object('key', cs.key,
                                  'state', cs.state,
                                  'enabled', c.enabled,
                                  'datetime', sc.datetime,
                                  'value', sc.value,
                                  'warning', sc.warning,
                                  'critical', sc.critical)) AS state_detail
FROM monitoring.checks c JOIN monitoring.check_states cs ON (c.check_id = cs.check_id)
JOIN monitoring.state_changes sc ON (sc.check_id = c.check_id AND sc.key = cs.key
                                     AND sc.datetime = (SELECT MAX(datetime)
                                                        FROM monitoring.state_changes sc2
                                                        WHERE sc2.check_id=c.check_id
                                                        AND sc2.key = cs.key
                                                        AND sc2.state = cs.state))
WHERE host_id = :host_id AND instance_id = :instance_id AND c.name = :check_name
    """  # noqa
    res = session.execute(query,
                          dict(host_id=host_id, instance_id=instance_id,
                               check_name=check_name))
    row = res.fetchone()
    c_row = dict(row)
    return c_row['state_detail']
