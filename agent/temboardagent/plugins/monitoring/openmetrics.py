# Declare and generates openmetrics sample from monitoring data stored in
# SQLite database.
#
# If possible, implement postgres_exporter and node_exporter metrics. Unlike
# prometheus, temBoard agent compute rates and diff in agent side. The open
# metrics must conform to prometheus exporter way : expose raw data (either
# gauge or counter) and let Prometheus query do computations.

import logging
import sys
from typing import List

from ...tools import fromisoformat


logger = logging.getLogger(__name__)
METADATAS = {}


class MetricMetadata:
    COUNTER = 'counter'
    GAUGE = 'gauge'

    def __init__(self, name, help_, type_='untyped'):
        self.name = name
        self.help_ = help_
        self.type_ = type_

    def format(self) -> List[str]:
        yield "# HELP {self.name} {self.help_}".format(self=self)
        yield "# TYPE {self.name} {self.type_}".format(self=self)


class Sample:
    def __init__(self, name, labels=None, value=1, timestamp=None):
        self.name = name
        self.labels = labels or {}
        self.value = value
        self.timestamp = timestamp

    def format(self) -> List[str]:
        labels = ','.join([
            '%s="%s"' % (name, value)
            for name, value in
            sorted(self.labels.items())
        ])
        if labels:
            labels = "{%s}" % labels
        if type(self.value) is str:
            raise Exception(
                "String value %s for %s." % (self.value, self.name))
        elif type(self.value) in (int, float):
            value = str(self.value)
        elif hasattr(self.value, 'timestamp'):
            value = str(self.value.timestamp())
        else:
            raise ValueError("Bad value {self.value}".format(self=self))

        tokens = [
            "{self.name}{labels}".format(self=self, labels=labels),
            value,
            str(self.timestamp or ""),
        ]
        yield " ".join(filter(None, tokens))

    def sort_key(self):
        return (self.name, sorted(self.labels.items()))


def format_open_metrics_lines(samples: List[Sample]) -> List[str]:
    described = set()
    for sample in sorted(samples, key=Sample.sort_key):
        if sample.name not in described:
            if described:
                yield ""
            yield from METADATAS[sample.name].format()
            described.add(sample.name)

        yield from sample.format()

    yield ""
    yield "# EOF"
    yield ""


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'node_os_info',
        help_=(
            "Operating system metadata, (see node_uname_info for kernel "
            "metadata)."),
        type_=MetricMetadata.GAUGE,
    ),
    MetricMetadata(
        'node_uname_info',
        help_=(
            "Labeled system information as provided by the uname system "
            "call."),
        type_=MetricMetadata.GAUGE,
    ),
    MetricMetadata(
        'pg_settings_max_connections',
        help_="Sets the maximum number of concurrent connections.",
        type_=MetricMetadata.GAUGE,
    ),
    # For compatibility with postgres_exporter.
    MetricMetadata(
        'pg_exporter_last_scrape_duration_seconds',
        help_="Duration of the last scrape of metrics from PostgresSQL.",
        type_=MetricMetadata.GAUGE,
    ),
    MetricMetadata(
        'pg_static',
        help_="Version string as reported by postgres",
    ),
    MetricMetadata(
        'pg_up',
        help_=(
            "Whether the last scrape of metrics from PostgreSQL was able to "
            "connect to the server (1 for yes, 0 for no)."),
        type_=MetricMetadata.GAUGE,
    ),
    # From
    # https://github.com/prometheus-community/postgres_exporter/blob/master/queries.yaml#L9-L15
    # Required by PostgreSQL Database dashboard variables.
    MetricMetadata(
        'pg_postmaster_start_time_seconds',
        help_="Time at which postmaster started",
        type_=MetricMetadata.GAUGE,
    ),
]})


def generate_samples(temboard_data) -> List[Sample]:
    instance = temboard_data['instances'][0]
    yield Sample(
        'node_os_info',
        dict(pretty_name=temboard_data['hostinfo']['os_flavor']),
    )
    nodename, _, domainname = instance['hostname'].partition('.')
    yield Sample(
        'node_uname_info',
        dict(
            domainename=domainname or '(none)',
            machine=temboard_data['hostinfo']['cpu_arch'],
            nodename=nodename,
            release=temboard_data['hostinfo']['os_version'],
            sysname=temboard_data['hostinfo']['os'],
        ),
    )

    yield Sample('pg_up')
    yield Sample(
        'pg_exporter_last_scrape_duration_seconds',
        value=0.0
    )
    yield Sample(
        'pg_postmaster_start_time_seconds',
        value=fromisoformat(instance['start_time']),
    )
    yield Sample(
        'pg_settings_max_connections',
        value=int(instance['max_connections']),
    )
    yield Sample(
        'pg_static',
        dict(
            short_version=instance['version'],
            # Extension of postgres_exporter labels.
            temboard_agent_version=temboard_data['version'],
            cluster_name=instance['local_name'],
        ),
    )

    mod = sys.modules[__name__]
    for probe, data in temboard_data['data'].items():
        if not data:
            continue

        generator_name = 'generate_%s_samples' % probe
        generator = getattr(mod, generator_name, None)
        if not generator:
            logger.debug("Can't export metrics from probe %s.", probe)
            raise Exception(probe)
            continue

        yield from generator(data, temboard_data['hostinfo'])


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'node_load1',
        help_="1m load average.",
        type_=MetricMetadata.GAUGE,
    ),
    MetricMetadata(
        'node_load5',
        help_="5m load average.",
        type_=MetricMetadata.GAUGE,
    ),
    MetricMetadata(
        'node_load15',
        help_="15m load average.",
        type_=MetricMetadata.GAUGE,
    ),
]})


def generate_loadavg_samples(data, hostinfo):
    for relative in '1', '5', '15':
        yield Sample(
            'node_load' + relative,
            value=float(data[0]['load' + relative]),
        )


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'node_cpu_seconds_total',
        help_="Seconds the CPUs spent in each mode.",
        type_=MetricMetadata.COUNTER,
    ),
]})


def generate_cpu_samples(data, hostinfo):
    for mode in 'idle', 'iowait', 'steal', 'system', 'user':
        for core in range(hostinfo['cpu_count']):
            yield Sample(
                'node_cpu_seconds_total',
                dict(cpu=core, mode=mode),
                # temBoard use global cpu data while node_exporter use per-core
                # data. Divide by core count to mimic per-core data.
                data[0]['time_' + mode] / 1000 / hostinfo['cpu_count'],
            )


METADATAS.update({m.name: m for m in [
    *[MetricMetadata(
        'node_memory_%s_bytes' % field,
        help_="Memory information field %s_bytes." % field,
        type_=MetricMetadata.GAUGE,
    ) for field in (
        'Buffers', 'Cached',
        'MemFree', 'MemTotal',
        'SwapTotal', 'SwapFree',
    )],
]})


def generate_memory_samples(data, hostinfo):
    yield Sample(
        'node_memory_Buffers_bytes',
        value=data[0]['mem_buffers'],
    )
    yield Sample(
        'node_memory_Cached_bytes',
        value=data[0]['mem_cached'],
    )
    yield Sample(
        'node_memory_MemFree_bytes',
        value=data[0]['mem_free'],
    )
    yield Sample(
        'node_memory_MemTotal_bytes',
        value=data[0]['mem_total'],
    )
    yield Sample(
        'node_memory_SwapFree_bytes',
        value=data[0]['swap_total'] - data[0]['swap_used'],
    )
    yield Sample(
        'node_memory_SwapTotal_bytes',
        value=data[0]['swap_total'],
    )


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'node_context_switches_total',
        help_="Total number of context switches.",
        type_=MetricMetadata.COUNTER,
    ),
    MetricMetadata(
        'node_fork_total',
        help_="Total number of forks.",
        type_=MetricMetadata.COUNTER,
    ),
    MetricMetadata(
        'node_procs_blocked',
        help_="Number of processes blocked waiting for I/O to complete.",
        type_=MetricMetadata.GAUGE,
    ),
    MetricMetadata(
        'node_procs_running',
        help_="Number of processes in runnable state.",
        type_=MetricMetadata.GAUGE,
    ),
    MetricMetadata(
        'xnode_procs_total',
        help_="Total number of processes (temBoard custom).",
        type_=MetricMetadata.GAUGE,
    ),
]})


def generate_process_samples(data, hostinfo):
    yield Sample(
        'node_context_switches_total',
        value=data[0]['context_switches'],
    )
    yield Sample(
        'node_fork_total',
        value=data[0]['forks'],
    )
    for field in 'blocked', 'running':
        yield Sample(
            'node_procs_' + field,
            value=data[0]['procs_' + field],
        )
    yield Sample(
        'xnode_procs_total',
        value=int(data[0]['procs_total']),
    )


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'node_filesystem_size_bytes',
        help_="Filesystem size in bytes.",
        type_=MetricMetadata.GAUGE,
    ),
    MetricMetadata(
        'node_filesystem_free_bytes',
        help_="Filesystem free space in bytes.",
        type_=MetricMetadata.GAUGE,
    ),
]})


def generate_filesystems_size_samples(data, hostinfo):
    for fs in data:
        yield Sample(
            'node_filesystem_size_bytes',
            dict(device=fs['device'], mountpoint=fs['mount_point']),
            fs['total'],
        )
        yield Sample(
            'node_filesystem_free_bytes',
            dict(device=fs['device'], mountpoint=fs['mount_point']),
            fs['total'] - fs['used'],
        )


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'pg_locks_count',
        help_="Number of locks",
        type_=MetricMetadata.GAUGE,
    ),
]})


def generate_locks_samples(data, hostinfo):
    lock_modes = (
        'access_share',
        'waiting_access_share',
        'row_share',
        'waiting_row_share',
        'row_exclusive',
        'waiting_row_exclusive',
        'share_update_exclusive',
        'waiting_share_update_exclusive',
        'share',
        'waiting_share',
        'share_row_exclusive',
        'waiting_share_row_exclusive',
        'exclusive',
        'waiting_exclusive',
        'access_exclusive',
        'waiting_access_exclusive',
        'siread',
    )
    for datdata in data:
        for mode in lock_modes:
            prommode = mode.replace('_', '')
            yield Sample(
                'pg_locks_count',
                dict(mode=prommode, datname=datdata['dbname']),
                datdata[mode],
            )


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'pg_stat_activity_count',
        help_="number of connections in this state",
        type_=MetricMetadata.GAUGE,
    ),
]})


def generate_sessions_samples(data, hostinfo):
    session_states = {
        'active': 'active',
        'disabled': 'disabled',
        'fastpath': 'fastpath function call',
        'idle': 'idle',
        'idle_in_xact': 'idle in transaction',
        'idle_in_xact_aborted': 'idle in transaction (aborted)',
    }
    for datdata in data:
        for state, promstate in session_states.items():
            yield Sample(
                'pg_stat_activity_count',
                dict(datname=datdata['dbname'], state=promstate),
                datdata[state]
            )


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'pg_stat_bgwriter_buffers_alloc',
        help_="Number of buffers allocated",
        type_=MetricMetadata.COUNTER,
    ),
    MetricMetadata(
        'pg_stat_bgwriter_buffers_backend',
        help_="Number of buffers written directly by a backend",
        type_=MetricMetadata.COUNTER,
    ),
    MetricMetadata(
        'pg_stat_bgwriter_buffers_backend_fsync',
        help_=(
            "Number of times a backend had to execute its own fsync call "
            "(normally the background writer handles those even when the "
            "backend does its own write)"
        ),
        type_=MetricMetadata.COUNTER,
    ),
    MetricMetadata(
        'pg_stat_bgwriter_buffers_checkpoint',
        help_="Number of buffers written during checkpoints",
        type_=MetricMetadata.COUNTER,
    ),
    MetricMetadata(
        'pg_stat_bgwriter_buffers_clean',
        help_="Number of buffers written by the background writer",
        type_=MetricMetadata.COUNTER,
    ),
    MetricMetadata(
        'pg_stat_bgwriter_checkpoint_sync_time',
        help_=(
            "Total amount of time that has been spent in the portion of "
            "checkpoint processing where files are synchronized to disk, "
            "in milliseconds"
        ),
        type_=MetricMetadata.COUNTER,
    ),
    MetricMetadata(
        'pg_stat_bgwriter_checkpoint_write_time',
        help_=(
            "Total amount of time that has been spent in the portion of "
            "checkpoint processing where files are written to disk, in "
            "milliseconds"
        ),
        type_=MetricMetadata.COUNTER,
    ),
    MetricMetadata(
        'pg_stat_bgwriter_checkpoints_req',
        help_="Number of requested checkpoints that have been performed",
        type_=MetricMetadata.COUNTER,
    ),
    MetricMetadata(
        'pg_stat_bgwriter_checkpoints_timed',
        help_="Number of scheduled checkpoints that have been performed",
        type_=MetricMetadata.COUNTER,
    ),
    MetricMetadata(
        'pg_stat_bgwriter_maxwritten_clean',
        help_=(
            "Number of times the background writer stopped a cleaning scan "
            "because it had written too many buffers"
        ),
        type_=MetricMetadata.COUNTER,
    ),
    MetricMetadata(
        'pg_stat_bgwriter_stats_reset',
        help_="Time at which these statistics were last reset",
        type_=MetricMetadata.COUNTER,
    ),
]})


def generate_bgwriter_samples(data, hostinfo):
    yield Sample(
        'pg_stat_bgwriter_stats_reset',
        value=fromisoformat(data[0]['stats_reset']),
    )

    bgwriter_stats = (
        'buffers_alloc',
        'buffers_backend',
        'buffers_backend_fsync',
        'buffers_clean',
        'buffers_checkpoint',
        'checkpoint_sync_time',
        'checkpoint_write_time',
        'checkpoints_timed',
        'checkpoints_req',
        'maxwritten_clean',
    )
    for stat in bgwriter_stats:
        yield Sample(
            'pg_stat_bgwriter_' + stat,
            value=data[0][stat],
        )


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'xpg_database_size_bytes',
        help_="Database total size",
        type_=MetricMetadata.GAUGE,
    ),
]})


def generate_db_size_samples(data, hostinfo):
    for datdata in data:
        yield Sample(
            'xpg_database_size_bytes',
            dict(datname=datdata['dbname']),
            datdata['size'],
        )


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'pg_stat_database_temp_bytes',
        help_=(
            "Total amount of data written to temporary files by queries in "
            "this database. All temporary files are counted, regardless of "
            "why the temporary file was created, and regardless of the "
            "log_temp_files setting.",
        ),
        type_=MetricMetadata.COUNTER,
    ),
]})


def generate_temp_files_size_delta_samples(data, hostinfo):
    for datdata in data:
        yield Sample(
            'pg_stat_database_temp_bytes',
            dict(datname=datdata['dbname']),
            datdata['size'],
        )


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'xpg_tablespace_size_bytes',
        help_="Tablespace total size",
        type_=MetricMetadata.GAUGE,
    ),
]})


def generate_tblspc_size_samples(data, hostinfo):
    for spcdata in data:
        yield Sample(
            'xpg_tablespace_size_bytes',
            dict(spcname=spcdata['spcname']),
            spcdata['size']
        )


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'xpg_wal_files_bytes_total',
        help_="Total size of all WALs",
        type_=MetricMetadata.GAUGE,
    ),
    MetricMetadata(
        'xpg_wal_files_total',
        help_="Total number of WALs",
        type_=MetricMetadata.GAUGE,
    ),
    MetricMetadata(
        'xpg_wal_files_archive_ready_total',
        help_="Total number of WALs ready for archiving.",
        type_=MetricMetadata.GAUGE,
    ),
    MetricMetadata(
        'xpg_wal_files_written_size_bytes',
        help_="Total bytes written in current WAL.",
        type_=MetricMetadata.COUNTER,
    ),
]})


def generate_wal_files_samples(data, hostinfo):
    yield Sample(
        'xpg_wal_files_total',
        value=data[0]['total'],
    )
    yield Sample(
        'xpg_wal_files_archive_ready_total',
        value=data[0]['archive_ready'],
    )
    yield Sample(
        'xpg_wal_files_bytes_total',
        value=data[0]['total_size'],
    )
    yield Sample(
        'xpg_wal_files_written_size_bytes',
        dict(current_wal_lsn=data[0]['current_location']),
        data[0]['written_size'],
    )


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'xpg_btree_bloat_ratio',
        help_="Bloat estimation of btree indexes in database.",
        type_=MetricMetadata.GAUGE,
    ),
]})


def generate_btree_bloat_samples(data, hostinfo):
    for datdata in data:
        yield Sample(
            'xpg_btree_bloat_ratio',
            dict(datname=datdata['dbname']),
            datdata['ratio'],
        )


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'xpg_heap_bloat_ratio',
        help_="Bloat estimation of table data in database.",
        type_=MetricMetadata.GAUGE,
    ),
]})


def generate_heap_bloat_samples(data, hostinfo):
    for datdata in data:
        yield Sample(
            'xpg_heap_bloat_ratio',
            dict(datname=datdata['dbname']),
            datdata['ratio'],
        )


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'pg_stat_database_xact_commit',
        help_=(
            "Number of transactions in this database that have been "
            "committed"
        ),
        type_=MetricMetadata.COUNTER,
    ),
    MetricMetadata(
        'pg_stat_database_xact_rollback',
        help_=(
            "Number of transactions in this database that have been rolled "
            "back"
        ),
        type_=MetricMetadata.COUNTER,
    ),
]})


def generate_xacts_samples(data, hostinfo):
    for datdata in data:
        yield Sample(
            'pg_stat_database_xact_commit',
            dict(datname=datdata['dbname']),
            datdata['n_commit'],
        )
        yield Sample(
            'pg_stat_database_xact_rollback',
            dict(datname=datdata['dbname']),
            datdata['n_rollback'],
        )


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'pg_stat_database_blks_hit',
        help_=(
            "Number of times disk blocks were found already in the buffer "
            "cache, so that a read was not necessary (this only includes hits "
            "in the PostgreSQL buffer cache, not the operating system's file "
            "system cache)"
        ),
        type_=MetricMetadata.COUNTER,
    ),
    MetricMetadata(
        'pg_stat_database_blks_read',
        help_="Number of disk blocks read in this database",
        type_=MetricMetadata.COUNTER,
    ),
]})


def generate_blocks_samples(data, hostinfo):
    for datdata in data:
        yield Sample(
            'pg_stat_database_blks_hit',
            dict(datname=datdata['dbname']),
            datdata['blks_hit'],
        )
        yield Sample(
            'pg_stat_database_blks_read',
            dict(datname=datdata['dbname']),
            datdata['blks_read'],
        )
        # let PromQL compute hitmiss ratio.


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'xpg_replication_up',
        help_="Streaming replication connection status",
        type_=MetricMetadata.GAUGE,
    ),
]})


def generate_replication_connection_samples(data, hostinfo):
    yield Sample(
        'xpg_replication_up',
        dict(upstream=data[0]['upstream']),
        data[0]['connected'],
    )


METADATAS.update({m.name: m for m in [
    MetricMetadata(
        'xpg_replication_lag_bytes',
        help_="Streaming replication lag",
        type_=MetricMetadata.GAUGE,
    ),
]})


def generate_replication_lag_samples(data, hostinfo):
    yield Sample(
        'xpg_replication_lag_bytes',
        value=data[0]['lag'],
    )
