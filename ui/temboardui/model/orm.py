import string
from secrets import choice

from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.query import Query
from sqlalchemy.schema import (
    Column,
    FetchedValue,
    ForeignKey,
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
)
from sqlalchemy.types import TIMESTAMP, BigInteger, Boolean, Integer, UnicodeText

from ..toolkit.utils import utcnow
from . import QUERIES

Model = declarative_base()


class ApiKeys(Model):
    __tablename__ = "apikeys"
    __table_args__ = {"schema": "application"}

    id = Column(BigInteger, primary_key=True)
    secret = Column(UnicodeText)
    comment = Column(UnicodeText)
    cdate = Column(TIMESTAMP(timezone=True))
    edate = Column(TIMESTAMP(timezone=True))

    _SECRET_LETTERS = string.ascii_letters + string.digits + "+/-_"

    @classmethod
    def generate_secret(cls, length=40):
        return "".join(choice(cls._SECRET_LETTERS) for _ in range(length))

    # See
    # https://docs.sqlalchemy.org/en/14/orm/queryguide.html#getting-orm-results-from-textual-and-core-statements

    @classmethod
    def insert(cls, secret, comment):
        return Query(cls).from_statement(
            text(QUERIES["apikeys-insert"])
            .bindparams(secret=secret, comment=comment)
            .columns(*cls.__mapper__.c.values())
        )

    @classmethod
    def select_active(cls):
        return Query(cls).from_statement(
            text(QUERIES["apikeys-select-active"]).columns(*cls.__mapper__.c.values())
        )

    @classmethod
    def delete(cls, id):
        return Query(cls).from_statement(
            text(QUERIES["apikeys-delete"])
            .bindparams(id=id)
            .columns(cls.id, cls.comment)
        )

    @classmethod
    def purge(cls):
        return Query(cls).from_statement(
            text(QUERIES["apikeys-purge"]).columns(cls.id, cls.comment)
        )

    @classmethod
    def select_secret(cls, secret):
        return Query(cls).from_statement(
            text(QUERIES["apikeys-select-secret"])
            .bindparams(secret=secret)
            .columns(*cls.__mapper__.c.values())
        )

    @property
    def expired(self):
        return self.edate < utcnow()


class Plugins(Model):
    __tablename__ = "plugins"
    __table_args__ = (
        PrimaryKeyConstraint("agent_address", "agent_port", "plugin_name"),
        ForeignKeyConstraint(
            ["agent_address", "agent_port"],
            ["application.instances.agent_address", "application.instances.agent_port"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        {"schema": "application"},
    )

    agent_address = Column(UnicodeText)
    agent_port = Column(Integer)
    plugin_name = Column(UnicodeText)


class InstanceGroups(Model):
    __tablename__ = "instance_groups"
    __table_args__ = (
        PrimaryKeyConstraint("agent_address", "agent_port", "group_name", "group_kind"),
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
        {"schema": "application"},
    )

    agent_address = Column(UnicodeText)
    agent_port = Column(Integer)
    group_name = Column(UnicodeText)
    group_kind = Column(UnicodeText, server_default=FetchedValue())


class RoleGroups(Model):
    __tablename__ = "role_groups"
    __table_args__ = (
        PrimaryKeyConstraint("role_name", "group_name", "group_kind"),
        ForeignKeyConstraint(
            ["group_name", "group_kind"],
            ["application.groups.group_name", "application.groups.group_kind"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        {"schema": "application"},
    )

    role_name = Column(UnicodeText, ForeignKey("application.roles.role_name"))
    group_name = Column(UnicodeText)
    group_kind = Column(UnicodeText)


class AccessRoleInstance(Model):
    __tablename__ = "access_role_instance"
    __table_args__ = (
        PrimaryKeyConstraint(
            "role_group_name",
            "role_group_kind",
            "instance_group_name",
            "instance_group_kind",
        ),
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
        {"schema": "application"},
    )

    role_group_name = Column(UnicodeText)
    role_group_kind = Column(UnicodeText)
    instance_group_name = Column(UnicodeText)
    instance_group_kind = Column(UnicodeText)


class Roles(Model):
    __tablename__ = "roles"
    __table_args__ = {"schema": "application"}

    role_name = Column(UnicodeText, primary_key=True)
    role_password = Column(UnicodeText)
    role_email = Column(UnicodeText)
    role_phone = Column(UnicodeText)
    is_active = Column(Boolean)
    is_admin = Column(Boolean)

    groups = relationship(
        RoleGroups,
        order_by=RoleGroups.group_name,
        backref="roles",
        cascade="save-update, merge, delete, delete-orphan",
    )

    @classmethod
    def count(cls):
        return text(QUERIES["users-count"]).columns(count=Integer)


class StubRole:
    # Fake object for roles not in database.
    def __init__(self, role_name):
        self.role_name = role_name


class Instances(Model):
    __tablename__ = "instances"
    __table_args__ = (
        PrimaryKeyConstraint("agent_address", "agent_port"),
        {"schema": "application"},
    )

    agent_address = Column(UnicodeText)
    agent_port = Column(Integer)
    hostname = Column(UnicodeText)
    pg_port = Column(Integer)
    notify = Column(Boolean, server_default=FetchedValue())
    comment = Column(UnicodeText)
    discover = Column(postgresql.JSONB)
    discover_date = Column(TIMESTAMP, server_default=FetchedValue())
    discover_etag = Column(UnicodeText)

    groups = relationship(
        InstanceGroups,
        order_by="InstanceGroups.group_name",
        backref="instances",
        cascade="save-update, merge, delete, delete-orphan",
        lazy="joined",
    )

    plugins = relationship(
        Plugins,
        order_by="Plugins.plugin_name",
        backref="instances",
        cascade="save-update, merge, delete, delete-orphan",
        lazy="joined",
    )

    def __str__(self):
        return f"{self.hostname}:{self.pg_port}"

    @classmethod
    def factory(
        cls,
        agent_address,
        agent_port,
        discover,
        discover_etag=None,
        notify=False,
        comment=None,
    ):
        return cls(
            agent_address=str(agent_address),
            agent_port=int(agent_port),
            discover=discover,
            discover_etag=discover_etag,
            pg_port=int(discover["postgres"]["port"]),
            hostname=discover["system"]["fqdn"],
            notify=bool(notify),
            comment=comment or "",
        )

    @classmethod
    def get(cls, agent_address, agent_port):
        return (
            Query(cls)
            .prefix_with("-- Instances.get\n")
            .filter(cls.agent_address == str(agent_address))
            .filter(cls.agent_port == int(agent_port))
        )

    @classmethod
    def count(cls):
        return text(QUERIES["instances-count"]).columns(count=Integer)

    @classmethod
    def all(cls):
        return Query(cls).from_statement(
            text(QUERIES["instances-all"]).columns(*cls.__mapper__.c.values())
        )

    # Compatibility from new JSONb discover to old column discover.
    @property
    def cpu(self):
        d = self.discover or {}
        return d.get("system", {}).get("cpu_count")

    @property
    def memory_size(self):
        d = self.discover or {}
        return d.get("system", {}).get("memory")

    @property
    def pg_data(self):
        d = self.discover or {}
        return d.get("postgres", {}).get("data_directory")

    @property
    def pg_version(self):
        d = self.discover or {}
        return d.get("postgres", {}).get("version")

    @property
    def pg_version_summary(self):
        d = self.discover or {}
        return d.get("postgres", {}).get("version_summary")

    def dashboard_url(self, app):
        scheme = "https" if app.config.temboard.ssl_key_file else "http"
        host = app.config.temboard.address
        port = app.config.temboard.port
        path = f"/server/{self.agent_address}/{self.agent_port}/dashboard"
        return f"{scheme}://{host}:{port}{path}"

    def asdict(self):
        return dict(
            hostname=self.hostname,
            pg_port=self.pg_port,
            agent_address=self.agent_address,
            agent_port=self.agent_port,
            groups=[group.group_name for group in self.groups],
            plugins=[plugin.plugin_name for plugin in self.plugins],
            comment=self.comment,
            notify=self.notify,
            discover=self.discover,
            discover_etag=self.discover_etag,
            discover_date=self.discover_date,
        )


class Groups(Model):
    __tablename__ = "groups"
    __table_args__ = (
        PrimaryKeyConstraint("group_name", "group_kind"),
        {"schema": "application"},
    )

    group_name = Column(UnicodeText)
    group_kind = Column(UnicodeText)
    group_description = Column(UnicodeText)

    ari = relationship(
        AccessRoleInstance,
        order_by=AccessRoleInstance.role_group_name,
        backref="groups",
        cascade="save-update, merge, delete, delete-orphan",
        foreign_keys=[
            AccessRoleInstance.instance_group_name,
            AccessRoleInstance.instance_group_kind,
        ],
    )
