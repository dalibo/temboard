import string
from secrets import choice

import sqlalchemy
from sqlalchemy import Column, Table, orm, schema, text, types
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query, relationship

from ..toolkit.utils import utcnow
from . import QUERIES

Model = declarative_base()

# For bridging ORM with raw SQL code, see
# https://docs.sqlalchemy.org/en/14/orm/queryguide.html#getting-orm-results-from-textual-and-core-statements


class ApiKey(Model):
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

    @classmethod
    def insert(cls, secret, comment):
        return Query(cls).from_statement(
            text(QUERIES["apikeys-insert"]).bindparams(secret=secret, comment=comment)
        )

    @classmethod
    def select_active(cls):
        return Query(cls).from_statement(text(QUERIES["apikeys-select-active"]))

    @classmethod
    def delete(cls, id):
        return Query(cls).from_statement(
            text(QUERIES["apikeys-delete"]).bindparams(id=id)
        )

    @classmethod
    def purge(cls):
        return Query(cls).from_statement(text(QUERIES["apikeys-purge"]))

    @classmethod
    def select_secret(cls, secret):
        return Query(cls).from_statement(
            text(QUERIES["apikeys-select-secret"]).bindparams(secret=secret)
        )

    @property
    def expired(self):
        return self.edate < utcnow()


class Plugin(Model):
    __tablename__ = "plugins"
    __table_args__ = (
        schema.PrimaryKeyConstraint("agent_address", "agent_port", "plugin_name"),
        schema.ForeignKeyConstraint(
            ["agent_address", "agent_port"],
            ["application.instances.agent_address", "application.instances.agent_port"],
        ),
        {"schema": "application"},
    )

    agent_address = Column(types.UnicodeText)
    agent_port = Column(types.Integer)
    plugin_name = Column(types.UnicodeText)

    instance = relationship("Instance", back_populates="plugins")

    @classmethod
    def insert(cls, instance, name):
        return Query(cls).from_statement(
            text(QUERIES["instance-enable-plugin"]).bindparams(
                agent_address=instance.agent_address,
                agent_port=instance.agent_port,
                name=name,
            )
        )

    @classmethod
    def delete(cls, instance, name):
        return text(QUERIES["instance-disable-plugin"]).bindparams(
            address=instance.agent_address, port=instance.agent_port, name=name
        )


memberships = Table(
    "memberships",
    Model.metadata,
    Column("id", primary_key=True),
    Column("role_name", schema.ForeignKey("application.roles.role_name")),
    Column("group_id", schema.ForeignKey("application.groups.id")),
    schema="application",
)


class Role(Model):
    __tablename__ = "roles"
    __table_args__ = {"schema": "application"}

    role_name = Column(types.UnicodeText, primary_key=True)
    role_password = Column(types.UnicodeText)
    role_email = Column(types.UnicodeText)
    role_phone = Column(types.UnicodeText)
    is_active = Column(types.Boolean)
    is_admin = Column(types.Boolean)

    groups = relationship(
        "Group", secondary=memberships, back_populates="members", lazy="raise"
    )

    @classmethod
    def count(cls):
        return text(QUERIES["roles-count"]).columns(count=types.Integer)

    @classmethod
    def all(cls):
        return (
            Query(cls)
            .from_statement(
                text(QUERIES["roles-all"]).columns(
                    Role.role_name,
                    Role.role_email,
                    Role.role_phone,
                    Role.is_active,
                    Role.is_admin,
                    Group.id,
                    Group.name,
                    Environment.id,
                    Environment.name,
                )
            )
            .options(orm.contains_eager(cls.groups).contains_eager(Group.environment))
        )

    @classmethod
    def delete(cls, name):
        return text(
            """DELETE FROM application.roles WHERE role_name = :name;"""
        ).bindparams(name=name)

    @classmethod
    def get(cls, name):
        return (
            Query(cls)
            .from_statement(
                text(QUERIES["roles-get"])
                .bindparams(name=name)
                .columns(
                    Role.role_name,
                    Role.role_email,
                    Role.role_phone,
                    Role.is_active,
                    Role.is_admin,
                    Group.id,
                    Group.name,
                    Environment.id,
                    Environment.name,
                )
            )
            .options(orm.contains_eager(cls.groups).contains_eager(Group.environment))
        )

    def asdict(self):
        return dict(
            name=self.role_name,
            email=self.role_email,
            phone=self.role_phone,
            active=self.is_active,
            admin=self.is_admin,
            groups=[g.name for g in self.groups],
            environments=[g.environment.name for g in self.groups],
        )

    def select_environments(self):
        return Query(Environment).from_statement(
            text(QUERIES["roles-select-environments"])
            .bindparams(role_name=self.role_name)
            .columns(Environment.id, Environment.name)
        )

    def select_instances(self):
        return Query(Instance).from_statement(
            text(QUERIES["roles-select-instances"])
            .bindparams(role_name=self.role_name)
            .columns(Instance.__mapper__.c.values())
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

    members = relationship(
        "Role", secondary=memberships, back_populates="groups", lazy="raise"
    )
    environment = relationship(
        "Environment", back_populates="dba_group", uselist=False, lazy="raise"
    )

    @classmethod
    def get(cls, name):
        return Query(cls).from_statement(
            text(QUERIES["group-get"]).bindparams(name=name)
        )

    @classmethod
    def delete(cls, name):
        return text(
            """DELETE FROM application.groups WHERE name = :name;"""
        ).bindparams(name=name)

    @classmethod
    def select_membership(self, name, username):
        return (
            text(QUERIES["group-select-membership"])
            .bindparams(group=name, role=username)
            .columns(
                username=types.UnicodeText,
                groupname=types.UnicodeText,
                description=types.UnicodeText,
            )
        )

    def insert_member(self, username):
        return text(QUERIES["group-insert-member"]).bindparams(
            group=self.name, role=username
        )

    @classmethod
    def delete_member(self, name, username):
        return text(QUERIES["group-delete-membership"]).bindparams(
            group=name, role=username
        )


class Environment(Model):
    __tablename__ = "environments"
    __table_args__ = {"schema": "application"}

    id = Column(types.BigInteger, primary_key=True)
    name = Column(types.UnicodeText)
    description = Column(types.UnicodeText)
    color = Column(types.UnicodeText)
    dba_group_id = Column(types.BigInteger, schema.ForeignKey("application.groups.id"))

    instances = relationship(
        "Instance",
        back_populates="environment",
        cascade="save-update, merge, delete, delete-orphan",
        lazy="raise",
    )
    dba_group = relationship(
        "Group", back_populates="environment", uselist=False, lazy="raise"
    )

    def __str__(self):
        return self.name

    @classmethod
    def get(cls, name):
        return (
            Query(cls)
            .from_statement(
                text(QUERIES["environments-get"])
                .bindparams(name=name)
                # Declare columns for disambiguation of id, name and description.
                .columns(*cls.__table__.c.values(), *Group.__table__.c.values())
            )
            .options(orm.contains_eager(cls.dba_group))
        )

    @classmethod
    def all(cls):
        return (
            Query(cls)
            .from_statement(text(QUERIES["environments-all"]))
            .options(orm.contains_eager(cls.dba_group))
        )

    @classmethod
    def delete(cls, name):
        return text(
            """DELETE FROM application.environments WHERE name = :name;"""
        ).bindparams(name=name)

    @classmethod
    def select_memberships(self, name):
        return (
            text(QUERIES["environment-memberships"])
            .bindparams(name=name)
            .columns(
                username=types.UnicodeText,
                groupname=types.UnicodeText,
                description=types.UnicodeText,
            )
        )

    def asdict(self):
        return dict(
            name=self.name,
            description=self.description,
            color=self.color,
            dba_group=self.dba_group.name,
        )


class Instance(Model):
    __tablename__ = "instances"
    __table_args__ = (
        schema.PrimaryKeyConstraint("agent_address", "agent_port"),
        {"schema": "application"},
    )

    agent_address = Column(types.UnicodeText)
    agent_port = Column(types.Integer)
    hostname = Column(types.UnicodeText)
    pg_port = Column(types.Integer)
    notify = Column(types.Boolean, server_default=schema.FetchedValue())
    comment = Column(types.UnicodeText)
    discover = Column(postgresql.JSONB)
    discover_date = Column(types.TIMESTAMP, server_default=schema.FetchedValue())
    discover_etag = Column(types.UnicodeText)
    environment_id = Column(
        types.Integer, schema.ForeignKey("application.environments.id")
    )

    environment = relationship("Environment", back_populates="instances", lazy="raise")
    plugins = relationship(Plugin, back_populates="instance", lazy="joined")

    def __str__(self):
        return f"{self.hostname}:{self.pg_port}"

    @classmethod
    def insert(
        cls,
        agent_address,
        agent_port,
        discover,
        discover_etag,
        environment,
        notify=False,
        comment=None,
    ):
        return (
            Query(cls)
            .from_statement(
                text(QUERIES["instances-insert"]).bindparams(
                    sqlalchemy.bindparam(
                        "discover", value=discover, type_=postgresql.JSONB
                    ),
                    agent_address=str(agent_address),
                    agent_port=int(agent_port),
                    discover_etag=discover_etag,
                    discover_date=utcnow(),
                    pg_port=int(discover["postgres"]["port"]),
                    hostname=discover["system"]["fqdn"],
                    environment=environment,
                    notify=bool(notify),
                    comment=comment or "",
                )
            )
            .options(orm.contains_eager(cls.plugins))
        )

    @classmethod
    def delete(cls, agent_address, agent_port):
        return text(
            """DELETE FROM application.instances WHERE agent_address = :address AND agent_port = :port;"""
        ).bindparams(address=str(agent_address), port=int(agent_port))

    @classmethod
    def get(cls, agent_address, agent_port):
        return (
            Query(cls)
            .from_statement(
                text(QUERIES["instance-get"])
                .bindparams(address=str(agent_address), port=int(agent_port))
                .columns(
                    *cls.__mapper__.c.values(),
                    *Plugin.__mapper__.c.values(),
                    *Environment.__mapper__.c.values(),
                    *Group.__mapper__.c.values(),
                )
            )
            .options(
                orm.contains_eager(cls.plugins),
                # chain contains_eager to reflect chained joins.
                orm.contains_eager(cls.environment).contains_eager(
                    Environment.dba_group
                ),
            )
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
        return (
            Query(cls)
            .from_statement(text(QUERIES["instances-all"]))
            .options(orm.contains_eager(cls.environment))
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
            environment=self.environment.name,
            plugins=[plugin.plugin_name for plugin in self.plugins],
            comment=self.comment,
            notify=self.notify,
            discover=self.discover,
            discover_etag=self.discover_etag,
            discover_date=self.discover_date,
        )

    def select_email_and_phone_for_notify(self):
        return (
            text(QUERIES["instance-select-email-and-phone-for-notify"])
            .bindparams(agent_address=self.agent_address, agent_port=self.agent_port)
            .columns(
                emails=types.ARRAY(types.UnicodeText),
                phones=types.ARRAY(types.UnicodeText),
            )
        )

    def has_dba(self, role_name):
        # DEPRECATED: Use ACL once implemented.
        return (
            text(QUERIES["instance-has-dba"])
            .bindparams(
                agent_address=self.agent_address,
                agent_port=self.agent_port,
                role_name=role_name,
            )
            .columns(has_dba=types.Boolean)
        )

    def enable_plugin(self, plugin):
        return Plugin.insert(self, plugin)

    def disable_plugin(self, plugin):
        return Plugin.delete(self, plugin)
