from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.schema import (
    CheckConstraint,
    Column,
    FetchedValue,
    ForeignKeyConstraint,
    MetaData,
    Table,
)
from sqlalchemy.sql import text
from sqlalchemy.types import Boolean, Integer, UnicodeText

metadata = MetaData()

groups = Table(
    "groups",
    metadata,
    Column("group_name", UnicodeText, nullable=False, primary_key=True),
    Column("group_description", UnicodeText),
    Column("group_kind", UnicodeText, nullable=False, primary_key=True),
    CheckConstraint("group_kind IN ('instance', 'role')"),
    schema="application",
)

instances = Table(
    "instances",
    metadata,
    Column("agent_address", UnicodeText, nullable=False, primary_key=True),
    Column("agent_port", Integer, nullable=False, primary_key=True),
    Column("hostname", UnicodeText, nullable=False),
    Column("pg_port", Integer),
    Column("notify", Boolean, nullable=False, server_default=FetchedValue()),
    Column("comment", UnicodeText),
    Column("discover", JSONB),
    Column("discover_date", TIMESTAMP, server_default=FetchedValue()),
    Column("discover_etag", UnicodeText),
    schema="application",
)

plugins = Table(
    "plugins",
    metadata,
    Column("agent_address", UnicodeText, nullable=False, primary_key=True),
    Column("agent_port", Integer, nullable=False, primary_key=True),
    Column("plugin_name", UnicodeText, nullable=False, primary_key=True),
    ForeignKeyConstraint(
        ["agent_address", "agent_port"],
        ["application.instances.agent_address", "application.instances.agent_port"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    ),
    schema="application",
)

instance_groups = Table(
    "instance_groups",
    metadata,
    Column("agent_address", UnicodeText, nullable=False, primary_key=True),
    Column("agent_port", Integer, nullable=False, primary_key=True),
    Column("group_name", UnicodeText, nullable=False, primary_key=True),
    Column("group_kind", UnicodeText, nullable=False, server_default=text("instance")),
    CheckConstraint("group_kind = 'instance'"),
    ForeignKeyConstraint(
        ["agent_address", "agent_port"],
        ["application.instances.agent_address", "application.instances.agent_port"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    ),
    ForeignKeyConstraint(
        ["group_name", "group_kind"],
        ["application.groups.group_name", "application.groups.group_kind"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    ),
    schema="application",
)

access_role_instance = Table(
    "access_role_instance",
    metadata,
    Column("role_group_name", UnicodeText, nullable=False, primary_key=True),
    Column("role_group_kind", UnicodeText, nullable=False, server_default=text("role")),
    Column("instance_group_name", UnicodeText, nullable=False, primary_key=True),
    Column(
        "instance_group_kind",
        UnicodeText,
        nullable=False,
        server_default=text("instance"),
    ),
    CheckConstraint("role_group_kind = 'role'"),
    CheckConstraint("instance_group_kind = 'instance'"),
    ForeignKeyConstraint(
        ["role_group_name", "role_group_kind"],
        ["application.groups.group_name", "application.groups.group_kind"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    ),
    ForeignKeyConstraint(
        ["instance_group_name", "instance_group_kind"],
        ["application.groups.group_name", "application.groups.group_kind"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    ),
    schema="application",
)
