import operator


def bootstrap_checks(hostinfo):
    # Default checks with thresholds to run against monitoring data

    # Loadaverage (value)
    # Global to host
    yield ("loadaverage", hostinfo['n_cpu'] / float(2), hostinfo['n_cpu'])
    # CPU (percent)
    # One per CPU
    yield ("cpu", 50, 80)
    # Memory usage (percent)
    # global
    yield ("memory", 50, 80)
    # Swap usage (percent)
    # Global to host
    yield ("swap", 30, 50)
    # Filesystems usage (percent)
    # One per filesystem
    yield ("fs", 80, 90)
    # Number of WAL files ready to be archived (value)
    # Global to postgres instance
    yield ("archive_ready", 10, 20)
    # Number of WAL files (value)
    # Global to postgres instance
    yield ("wal_files", 50, 100)
    # Number of transaction rollback (value)
    # One per DB
    yield ("xacts_rollback", 10, 20)
    # Cache hitratio (percent)
    # One per DB
    yield ("hitratio", 90, 80)
    # Client sessions vs max_connections (percent)
    # Global to postgres instance
    yield ("sessions", 80, 90)
    # Waiting sessions (value)
    # One per DB
    yield ("waiting", 5, 10)


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
            _data[r['dbname']] = int(r['hitmiss_ratio']) \
                if int(r['blks_read']) + int(r['blks_hit']) > 0 else 100
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


check_specs = dict(
    loadaverage=dict(
        type='system',
        description='Loadaverage',
        preprocess=PreProcess.loadaverage,
        message='{value} is greater than {threshold}',
        operator=operator.gt,
    ),
    cpu=dict(
        type='system',
        description='CPU usage',
        preprocess=PreProcess.cpu,
        message='{value}% is greater than {threshold}%',
        operator=operator.gt,
    ),
    memory=dict(
        type='system',
        description='Memory usage',
        preprocess=PreProcess.memory,
        message='{value}% is greater than {threshold}%',
        operator=operator.gt,
    ),
    swap=dict(
        type='system',
        description='Swap usage',
        preprocess=PreProcess.swap,
        message='{value}% is greater than {threshold}%',
        operator=operator.gt,
    ),
    fs=dict(
        type='system',
        description='File systems usage',
        preprocess=PreProcess.fs,
        message='{key}: {value}% is greater than {threshold}%',
        operator=operator.gt,
    ),
    archive_ready=dict(
        type='postgres',
        description='WAL files ready to be archived',
        preprocess=PreProcess.archive_ready,
        message='{value} is greater than {threshold}',
        operator=operator.gt,
    ),
    wal_files=dict(
        type='postgres',
        description='WAL files',
        preprocess=PreProcess.wal_files,
        message='{value} is greater than {threshold}',
        operator=operator.gt,
    ),
    xacts_rollback=dict(
        type='postgres',
        description='Rollbacked transactions',
        preprocess=PreProcess.xacts_rollback,
        message='{key}: {value} is greater than {threshold}',
        operator=operator.gt,
    ),
    hitratio=dict(
        type='postgres',
        description='Cache Hit Ratio',
        preprocess=PreProcess.hitratio,
        message='{key}: {value} is less than {threshold}',
        operator=operator.lt,
    ),
    sessions=dict(
        type='postgres',
        description='Client sessions',
        preprocess=PreProcess.sessions,
        message='{value} is greater than {threshold}',
        operator=operator.gt,
    ),
    waiting=dict(
        type='postgres',
        description='Waiting sessions',
        preprocess=PreProcess.waiting,
        message='{key}: {value} is greater than {threshold}',
        operator=operator.gt,
    ),
)
