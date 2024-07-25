import string
from secrets import choice

from sqlalchemy import Column, Table, schema, text, types
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query, relationship

from ..toolkit.utils import utcnow
from . import QUERIES

Model = declarative_base()


class ApiKeys(Model):
    __tablename__ = "apikeys"
    __table_args__ = {"schema": "application"}

    id = Column(types.BigInteger, primary_key=True)
    secret = Column(types.UnicodeText)
    comment = Column(types.UnicodeText)
    cdate = Column(types.TIMESTAMP(timezone=True))
    edate = Column(types.TIMESTAMP(timezone=True))

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
        schema.PrimaryKeyConstraint("agent_address", "agent_port", "plugin_name"),
        schema.ForeignKeyConstraint(
            ["agent_address", "agent_port"],
            ["application.instances.agent_address", "application.instances.agent_port"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        {"schema": "application"},
    )

    agent_address = Column(types.UnicodeText)
    agent_port = Column(types.Integer)
    plugin_name = Column(types.UnicodeText)


class InstanceGroups(Model):
    __tablename__ = "instance_groups"
    __table_args__ = (
        schema.PrimaryKeyConstraint(
            "agent_address", "agent_port", "group_name", "group_kind"
        ),
        schema.ForeignKeyConstraint(
            ["agent_address", "agent_port"],
            ["application.instances.agent_address", "application.instances.agent_port"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        schema.ForeignKeyConstraint(
            ["group_name", "group_kind"],
            ["application.groups.group_name", "application.groups.group_kind"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        {"schema": "application"},
    )

    agent_address = Column(types.UnicodeText)
    agent_port = Column(types.Integer)
    group_name = Column(types.UnicodeText)
    group_kind = Column(types.UnicodeText, server_default=schema.FetchedValue())


class RoleGroups(Model):
    __tablename__ = "role_groups"
    __table_args__ = (
        schema.PrimaryKeyConstraint("role_name", "group_name", "group_kind"),
        schema.ForeignKeyConstraint(
            ["group_name", "group_kind"],
            ["application.groups.group_name", "application.groups.group_kind"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        {"schema": "application"},
    )

    role_name = Column(
        types.UnicodeText, schema.ForeignKey("application.roles.role_name")
    )
    group_name = Column(types.UnicodeText)
    group_kind = Column(types.UnicodeText)


class AccessRoleInstance(Model):
    __tablename__ = "access_role_instance"
    __table_args__ = (
        schema.PrimaryKeyConstraint(
            "role_group_name",
            "role_group_kind",
            "instance_group_name",
            "instance_group_kind",
        ),
        schema.ForeignKeyConstraint(
            ["role_group_name", "role_group_kind"],
            ["application.groups.group_name", "application.groups.group_kind"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        schema.ForeignKeyConstraint(
            ["instance_group_name", "instance_group_kind"],
            ["application.groups.group_name", "application.groups.group_kind"],
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        {"schema": "application"},
    )

    role_group_name = Column(types.UnicodeText)
    role_group_kind = Column(types.UnicodeText)
    instance_group_name = Column(types.UnicodeText)
    instance_group_kind = Column(types.UnicodeText)


memberships = Table(
    "memberships",
    Model.metadata,
    Column(
        "role_name", schema.ForeignKey("application.roles.role_name"), primary_key=True
    ),
    Column("group_id", schema.ForeignKey("application.groups.id"), primary_key=True),
    schema="application",
)


class Roles(Model):
    __tablename__ = "roles"
    __table_args__ = {"schema": "application"}

    role_name = Column(types.UnicodeText, primary_key=True)
    role_password = Column(types.UnicodeText)
    role_email = Column(types.UnicodeText)
    role_phone = Column(types.UnicodeText)
    is_active = Column(types.Boolean)
    is_admin = Column(types.Boolean)

    groups = relationship("Group", secondary=memberships, back_populates="members")

    @classmethod
    def count(cls):
        return text(QUERIES["users-count"]).columns(count=types.Integer)

    def select_environments(self):
        return Query(Environment).from_statement(
            text(QUERIES["roles-select-environments"])
            .bindparams(role_name=self.role_name)
            .columns(Environment.id, Environment.name)
        )

    def select_instances(self):
        return Query(Instances).from_statement(
            text(QUERIES["roles-select-instances"])
            .bindparams(role_name=self.role_name)
            .columns(Instances.__mapper__.c.values())
        )


class StubRole:
    # Fake object for roles not in database.
    def __init__(self, role_name):
        self.role_name = role_name


class Group(Model):
    __tablename__ = "groups"
    __table_args__ = {"schema": "application"}

    id = Column(types.BigInteger, primary_key=True)
    name = Column(types.UnicodeText)
    description = Column(types.UnicodeText)
    cdate = Column(types.TIMESTAMP(timezone=True))

    members = relationship("Roles", secondary=memberships)
    environment = relationship("Environment", back_populates="dba_group", uselist=False)


class Environment(Model):
    __tablename__ = "environments"
    __table_args__ = {"schema": "application"}

    id = Column(types.BigInteger, primary_key=True)
    name = Column(types.UnicodeText)
    description = Column(types.UnicodeText)
    color = Column(types.UnicodeText)
    cdate = Column(types.TIMESTAMP(timezone=True))
    dba_group_id = Column(types.BigInteger, schema.ForeignKey("application.groups.id"))

    instances = relationship(
        "Instances",
        back_populates="environment",
        cascade="save-update, merge, delete, delete-orphan",
    )
    dba_group = relationship("Group", back_populates="environment", uselist=False)

    def __str__(self):
        return self.name

    @classmethod
    def get(cls, name):
        return Query(cls).from_statement(
            text(QUERIES["environments-get"])
            .bindparams(name=name)
            .columns(cls.__mapper__.c.values())
        )


class Instances(Model):
    __tablename__ = "instances"
    __table_args__ = {"schema": "application"}

    agent_address = Column(types.UnicodeText, primary_key=True)
    agent_port = Column(types.Integer, primary_key=True)
    hostname = Column(types.UnicodeText)
    pg_port = Column(types.Integer)
    notify = Column(types.Boolean)
    comment = Column(types.UnicodeText)
    discover = Column(postgresql.JSONB)
    discover_date = Column(postgresql.TIMESTAMP)
    discover_etag = Column(types.UnicodeText)
    environment_id = Column(
        types.Integer, schema.ForeignKey("application.environments.id")
    )

    environment = relationship("Environment", back_populates="instances")

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
        environment=None,
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
            environment=environment,
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
    def select_for_home(cls, role_name):
        return (
            text(QUERIES["instances-select-for-home"])
            .bindparams(role_name=role_name)
            .columns(
                agent_address=types.UnicodeText,
                agent_port=types.Integer,
                hostname=types.UnicodeText,
                pg_port=types.Integer,
                pg_data=types.UnicodeText,
                pg_version=types.UnicodeText,
                pg_version_summary=types.UnicodeText,
                groups=types.ARRAY(types.UnicodeText),
                plugins=types.ARRAY(types.UnicodeText),
                available=types.Boolean,
                checks=postgresql.JSONB,
            )
        )

    @classmethod
    def count(cls):
        return text(QUERIES["instances-count"]).columns(count=types.Integer)

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

    def has_dba(self, role_name):
        # DEPRECATED: Use ACL once implemented.
        return (
            text(QUERIES["instance-is-dba"])
            .bindparams(instance_id=self.id, role_name=role_name)
            .columns(has_dba=types.Boolean)
        )
