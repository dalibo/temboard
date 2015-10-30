"""
Mapping of the database for use with SQLAlchemy.
"""

from sqlalchemy.sql import text

from sqlalchemy.schema import (
    MetaData, Table, Column,
    ForeignKey, CheckConstraint, ForeignKeyConstraint)
from sqlalchemy.types import (
    Integer, UnicodeText, BigInteger,
    Boolean, DateTime, Interval, Float)
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, JSON

metadata = MetaData()

hosts = Table(
    'hosts', metadata,
    Column('hostname', UnicodeText, primary_key=True),
    Column('os', UnicodeText, nullable=False),
    Column('os_version', UnicodeText, nullable=False),
    Column('os_flavour', UnicodeText),
    Column('cpu_count', Integer),
    Column('cpu_arch', UnicodeText),
    Column('memory_size', BigInteger),
    Column('swap_size', BigInteger),
    Column('virtual', Boolean),
    schema = "supervision")

instances = Table(
    'instances', metadata,
    Column('hostname', UnicodeText,
           ForeignKey("supervision.hosts.hostname"),
           nullable=False,
           primary_key=True,
           ),
    Column('port', Integer, primary_key=True),
    Column('agent_key', UnicodeText),
    Column('local_name', UnicodeText, nullable=False,),
    Column('version', UnicodeText, nullable=False,),
    Column('version_num', Integer, nullable=False,),
    Column('data_directory', UnicodeText, nullable=False),
    Column('sysuser', UnicodeText,),
    Column('standby', Boolean, nullable=False, server_default=text('False')),
    schema = "supervision")

metric_sessions = Table(
    'metric_sessions', metadata,
    Column('datetime', DateTime(timezone=True),
           primary_key=True),
    Column('hostname', UnicodeText,
           primary_key=True),
    Column('port', Integer,
           primary_key=True),
    Column('dbname', UnicodeText, nullable=False),
    Column('active', Integer, nullable=False),
    Column('waiting', Integer, nullable=False),
    Column('idle', Integer, nullable=False),
    Column('idle_in_xact', Integer, nullable=False),
    Column('idle_in_xact_aborted', Integer, nullable=False),
    Column('fastpath', Integer, nullable=False),
    Column('disabled', Integer, nullable=False),
    Column('no_priv', Integer, nullable=False),
    ForeignKeyConstraint(
        ['hostname', 'port'],
        ['supervision.instances.hostname',
         'supervision.instances.port']),
    schema = "supervision")


metric_xacts = Table(
    'metric_xacts', metadata,
    Column('datetime', DateTime(timezone=True),
           primary_key=True),
    Column('hostname', UnicodeText, primary_key=True),
    Column('port', Integer, primary_key=True),
    Column('dbname', UnicodeText, nullable=False),
    Column('measure_interval', Interval, nullable=False),
    Column('n_commit', BigInteger, nullable=False),
    Column('n_rollback', BigInteger, nullable=False),
    ForeignKeyConstraint(
        ['hostname', 'port'],
        ['supervision.instances.hostname',
         'supervision.instances.port']),
    schema = "supervision")


metric_locks = Table(
    'metric_locks', metadata,
    Column('datetime', DateTime(timezone=True),
           primary_key=True),
    Column('hostname', UnicodeText, primary_key=True),
    Column('port', Integer, primary_key=True),
    Column('dbname', UnicodeText, nullable=False),
    Column('access_share', Integer, nullable=False),
    Column('row_share', Integer, nullable=False),
    Column('row_exclusive', Integer, nullable=False),
    Column('share_update_exclusive', Integer, nullable=False),
    Column('share', Integer, nullable=False),
    Column('share_row_exclusive', Integer, nullable=False),
    Column('exclusive', Integer, nullable=False),
    Column('access_exclusive', Integer, nullable=False),
    Column('siread', Integer, nullable=False),
    Column('waiting_access_share', Integer, nullable=False),
    Column('waiting_row_share', Integer, nullable=False),
    Column('waiting_row_exclusive', Integer, nullable=False),
    Column('waiting_share_update_exclusive', Integer, nullable=False),
    Column('waiting_share', Integer, nullable=False),
    Column('waiting_share_row_exclusive', Integer, nullable=False),
    Column('waiting_exclusive', Integer, nullable=False),
    Column('waiting_access_exclusive', Integer, nullable=False),
    ForeignKeyConstraint(
        ['hostname', 'port'],
        ['supervision.instances.hostname',
         'supervision.instances.port']),
    schema = "supervision")


metric_blocks = Table(
    'metric_blocks', metadata,
    Column('datetime', DateTime(timezone=True),
           primary_key=True),
    Column('hostname', UnicodeText, primary_key=True),
    Column('port', Integer, primary_key=True),
    Column('dbname', UnicodeText, nullable=False),

    Column('measure_interval', Interval, nullable=False),
    Column('blks_read', BigInteger, nullable=False),
    Column('blks_hit', BigInteger, nullable=False),
    Column('hitmiss_ratio', Float, nullable=False),
    ForeignKeyConstraint(
        ['hostname', 'port'],
        ['supervision.instances.hostname',
         'supervision.instances.port']),
    schema = "supervision")


metric_bgwriter = Table(
    'metric_bgwriter', metadata,

    Column('datetime', DateTime(timezone=True), primary_key=True),
    Column('hostname', UnicodeText, primary_key=True),
    Column('port', Integer, primary_key=True),
    ForeignKeyConstraint(['hostname', 'port'],
                         ['supervision.instances.hostname', 'supervision.instances.port']),
    Column('measure_interval', Interval, nullable=False),
    Column('checkpoints_timed', BigInteger, nullable=False),
    Column('checkpoints_req', BigInteger, nullable=False),
    Column('checkpoint_write_time', DOUBLE_PRECISION, nullable=True),
    Column('checkpoint_sync_time', DOUBLE_PRECISION, nullable=True),
    Column('buffers_checkpoint', BigInteger, nullable=False),
    Column('buffers_clean', BigInteger, nullable=False),
    Column('maxwritten_clean', BigInteger, nullable=False),
    Column('buffers_backend', BigInteger, nullable=False),
    Column('buffers_backend_fsync', BigInteger, nullable=True),
    Column('buffers_alloc', BigInteger, nullable=False),
    schema = "supervision")


metric_db_size = Table(
    'metric_db_size', metadata,
    Column('datetime', DateTime(timezone=True), primary_key=True),
    Column('hostname', UnicodeText, primary_key=True),
    Column('port', Integer, primary_key=True),
    Column('dbname', UnicodeText, nullable=False),
    ForeignKeyConstraint(
        ['hostname', 'port'],
        ['supervision.instances.hostname',
         'supervision.instances.port']),
    Column('size', BigInteger, nullable=False),
    schema = "supervision")


metric_tblspc_size = Table(
    'metric_tblspc_size', metadata,
    Column('datetime', DateTime(timezone=True), primary_key=True),
    Column('hostname', UnicodeText, primary_key=True),
    Column('port', Integer, primary_key=True),
    Column('spcname', UnicodeText, primary_key=True),
    ForeignKeyConstraint(['hostname', 'port'],
                         ['supervision.instances.hostname',
                          'supervision.instances.port']),
    Column('size', BigInteger, nullable=False),
    schema = "supervision")


metric_filesystems_size = Table(
    'metric_filesystems_size', metadata,
    Column('datetime', DateTime(timezone=True), primary_key=True),
    Column('hostname', UnicodeText, primary_key=True),
    Column('mount_point', UnicodeText, primary_key=True),
    ForeignKeyConstraint(['hostname'],
                         ['supervision.hosts.hostname']),
    Column('used', BigInteger, nullable=False),
    Column('total', BigInteger, nullable=False),
    schema = "supervision")


metric_temp_files_size_tblspc = Table(
    'metric_temp_files_size_tblspc', metadata,
    Column('datetime', DateTime(timezone=True), primary_key=True),
    Column('hostname', UnicodeText, primary_key=True),
    Column('port', Integer, primary_key=True),
    Column('spcname', UnicodeText, nullable=False),

    ForeignKeyConstraint(['hostname', 'port'],
                         ['supervision.instances.hostname',
                          'supervision.instances.port']),
    Column('size', BigInteger, nullable=False),
    schema = "supervision")


metric_temp_files_size_db = Table(
    'metric_temp_files_size_db', metadata,
    Column('datetime', DateTime(timezone=True), primary_key=True),
    Column('hostname', UnicodeText, primary_key=True),
    Column('port', Integer, primary_key=True),
    Column('dbname', UnicodeText, nullable=False),
    ForeignKeyConstraint(['hostname', 'port'],
                         ['supervision.instances.hostname',
                          'supervision.instances.port']),
    Column('size', BigInteger, nullable=False),
    schema = "supervision")


metric_wal_files = Table(
    'metric_wal_files', metadata,
    Column('datetime', DateTime(timezone=True), primary_key=True),
    Column('hostname', UnicodeText, primary_key=True),
    Column('port', Integer, primary_key=True),
    ForeignKeyConstraint(['hostname', 'port'],
                         ['supervision.instances.hostname', 'supervision.instances.port']),
    Column('measure_interval', Interval, nullable=False),
    Column('written_size', BigInteger, nullable=False),
    Column('total_size', BigInteger, nullable=False),
    Column('current_location', UnicodeText, nullable=False),
    Column('total', Integer, nullable=False),
    Column('archive_ready', Integer, nullable=False),
    schema = "supervision")

metric_cpu = Table(
    'metric_cpu', metadata,
    Column('datetime', DateTime(timezone=True), primary_key=True),
    Column('hostname', UnicodeText, ForeignKey('supervision.hosts.hostname'),
           primary_key=True),
    Column('cpu', UnicodeText, primary_key=True),
    Column('measure_interval', Interval, nullable=False),
    Column('time_user', BigInteger, nullable=False),
    Column('time_system', BigInteger, nullable=False),
    Column('time_idle', BigInteger, nullable=False),
    Column('time_iowait', BigInteger, nullable=False),
    Column('time_steal', BigInteger, nullable=False),
    schema = "supervision")

metric_process = Table(
    'metric_process', metadata,
    Column('datetime', DateTime(timezone=True), primary_key=True),
    Column('hostname', UnicodeText, ForeignKey('supervision.hosts.hostname'),
           primary_key=True),
    Column('measure_interval', Interval, nullable=False),
    Column('context_switches', BigInteger, nullable=False),
    Column('forks', BigInteger, nullable=False),
    Column('procs_running', Integer, nullable=False),
    Column('procs_blocked', Integer, nullable=False),
    Column('procs_total', Integer, nullable=False),
    schema = "supervision")


metric_memory = Table(
    'metric_memory', metadata,
    Column('datetime', DateTime(timezone=True), primary_key=True),
    Column('hostname', UnicodeText, ForeignKey('supervision.hosts.hostname'),
           primary_key=True),
    Column('mem_total', BigInteger, nullable=False),
    Column('mem_used', BigInteger, nullable=False),
    Column('mem_free', BigInteger, nullable=False),
    Column('mem_buffers', BigInteger, nullable=False),
    Column('mem_cached', BigInteger, nullable=False),
    Column('swap_total', BigInteger, nullable=False),
    Column('swap_used', BigInteger, nullable=False),
    schema = "supervision")


metric_loadavg = Table(
    'metric_loadavg', metadata,
    Column('datetime', DateTime(timezone=True), primary_key=True),
    Column('hostname', UnicodeText, ForeignKey('supervision.hosts.hostname'),
           primary_key=True),
    Column('load1', Float, nullable=False),
    Column('load5', Float, nullable=False),
    Column('load15', Float, nullable=False),
    schema = "supervision")


metric_vacuum_analyze = Table(
    'metric_vacuum_analyze', metadata,
    Column('datetime', DateTime(timezone=True), nullable=False),
    Column('dbname', UnicodeText, primary_key=True),
    Column('hostname', UnicodeText, primary_key=True),
    Column('port', Integer, primary_key=True),
    Column('measure_interval', Interval, nullable=False),
    Column('n_vacuum', Integer, nullable=False),
    Column('n_analyze', Integer, nullable=False),
    Column('n_autovacuum', Integer, nullable=False),
    Column('n_autoanalyze', Integer, nullable=False),
    ForeignKeyConstraint(['hostname', 'port'],
                         ['supervision.instances.hostname',
                          'supervision.instances.port']),
    schema = "supervision")


metric_replication = Table(
    'metric_replication', metadata,
    Column('datetime', DateTime(timezone=True), nullable=False,
           primary_key=True),
    Column('hostname', UnicodeText, primary_key=True),
    Column('port', Integer, primary_key=True),
    ForeignKeyConstraint(['hostname', 'port'],
                         ['supervision.instances.hostname', 'supervision.instances.port']),
    Column('receive_location', UnicodeText, nullable=False),
    Column('replay_location', UnicodeText, nullable=False),
    schema = "supervision")
