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
    Integer,
    UnicodeText,
    BigInteger,
    Boolean,
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
