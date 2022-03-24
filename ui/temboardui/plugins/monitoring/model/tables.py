"""
Mapping of the database for use with SQLAlchemy.
"""

from sqlalchemy.sql import text

from sqlalchemy.schema import (
    MetaData,
    Table,
    Column,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.types import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    REAL,
    UnicodeText,
)

metadata = MetaData()

hosts = Table(
    'hosts', metadata,
    Column('host_id', Integer, primary_key=True),
    Column('hostname', UnicodeText, nullable=False, unique=True),
    Column('os', UnicodeText, nullable=False),
    Column('os_version', UnicodeText, nullable=False),
    Column('os_flavour', UnicodeText),
    Column('cpu_count', Integer),
    Column('cpu_arch', UnicodeText),
    Column('memory_size', BigInteger),
    Column('swap_size', BigInteger),
    Column('virtual', Boolean),
    schema="monitoring")

instances = Table(
    'instances', metadata,
    Column('instance_id', Integer, primary_key=True),
    Column('host_id', Integer,
           ForeignKey("monitoring.hosts.host_id"),
           nullable=False,
           ),
    Column('port', Integer, nullable=False),
    Column('local_name', UnicodeText, nullable=False,),
    Column('version', UnicodeText, nullable=False,),
    Column('version_num', Integer, nullable=False,),
    Column('data_directory', UnicodeText, nullable=False),
    Column('sysuser', UnicodeText,),
    Column('standby', Boolean, nullable=False, server_default=text('False')),
    UniqueConstraint('host_id', 'port'),
    schema="monitoring")

checks = Table(
    'checks', metadata,
    Column('check_id', Integer, primary_key=True),
    Column('host_id', Integer,
           ForeignKey("monitoring.hosts.host_id"),
           nullable=False,
           ),
    Column('instance_id', Integer,
           ForeignKey("monitoring.instances.instance_id"),
           nullable=True,
           ),
    Column('enabled', Boolean, nullable=False),
    Column('name', UnicodeText, nullable=False),
    Column('warning', REAL),
    Column('critical', REAL),
    Column('description', UnicodeText),
    schema="monitoring")

checkstates = Table(
    'check_states', metadata,
    Column('check_id', Integer,
           ForeignKey("monitoring.checks.check_id"),
           nullable=False, primary_key=True),
    Column('key', UnicodeText, nullable=True, primary_key=True),
    Column('state', UnicodeText, nullable=False),
    schema="monitoring")

collector_status = Table(
    'collector_status',
    metadata,
    Column('instance_id', Integer,
           ForeignKey("monitoring.instances.instance_id"),
           primary_key=True),
    Column('last_pull', DateTime, nullable=True),
    Column('last_push', DateTime, nullable=True),
    Column('last_insert', DateTime, nullable=True),
    Column('status', UnicodeText),
    schema="monitoring",
)
