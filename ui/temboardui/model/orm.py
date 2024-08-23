import string
from secrets import choice

import sqlalchemy
from sqlalchemy import Column, orm, schema, text, types
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query, joinedload, relationship

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

    @classmethod
    def insert(cls, instance, name):
        return Query(cls).from_statement(
            text(QUERIES["instance-enable-plugin"]).bindparams(
                agent_address=instance.agent_address,
                agent_port=instance.agent_port,
                name=name,
            )
        )


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

    @classmethod
    def insert(cls, instance, group):
        return Query(cls).from_statement(
            text(QUERIES["instance-groups-insert"]).bindparams(
                agent_address=instance.agent_address,
                agent_port=instance.agent_port,
                group_name=group.group_name,
                group_kind=group.group_kind,
            )
        )


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

    @classmethod
    def insert(cls, role, instance):
        return (
            sqlalchemy.insert(cls.__table__)
            .returning(*cls.__mapper__.c.values())
            .values(
                role_group_kind="role",
                role_group_name=role,
                instance_group_kind="instance",
                instance_group_name=instance,
            )
        )

    @classmethod
    def delete(cls, role, instance):
        return sqlalchemy.delete(cls.__table__).where(
            cls.role_group_name == role, cls.instance_group_name == instance
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

    groups = relationship(
        RoleGroups,
        order_by=RoleGroups.group_name,
        backref="roles",
        cascade="save-update, merge, delete, delete-orphan",
    )

    @classmethod
    def count(cls):
        return text(QUERIES["users-count"]).columns(count=types.Integer)

    @classmethod
    def all(cls):
        return (
            Query(cls)
            .from_statement(
                text(QUERIES["roles-all"]).columns(
                    Roles.role_name,
                    Roles.role_email,
                    Roles.role_phone,
                    Roles.is_active,
                    Roles.is_admin,
                    RoleGroups.role_name,
                    RoleGroups.group_name,
                    RoleGroups.group_kind,
                )
            )
            .options(orm.contains_eager(cls.groups))
        )

    @classmethod
    def insert(cls, name, password):
        return Query(cls).from_statement(
            text(QUERIES["roles-insert"]).bindparams(name=name, password=password)
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
                    Roles.role_name,
                    Roles.role_email,
                    Roles.role_phone,
                    Roles.is_active,
                    Roles.is_admin,
                    RoleGroups.role_name,
                    RoleGroups.group_name,
                    RoleGroups.group_kind,
                )
            )
            .options(orm.contains_eager(cls.groups))
        )

    def asdict(self):
        return dict(
            name=self.role_name,
            email=self.role_email,
            phone=self.role_phone,
            active=self.is_active,
            admin=self.is_admin,
            groups=[g.group_name for g in self.groups],
        )


class StubRole:
    # Fake object for roles not in database.
    def __init__(self, role_name):
        self.role_name = role_name


class Instances(Model):
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
    def insert(
        cls,
        agent_address,
        agent_port,
        discover,
        discover_etag,
        notify=False,
        comment=None,
    ):
        return Query(cls).from_statement(
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
                notify=bool(notify),
                comment=comment or "",
            )
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
            .prefix_with("-- Instances.get\n")
            .filter(cls.agent_address == str(agent_address))
            .filter(cls.agent_port == int(agent_port))
            .options(joinedload("groups"), joinedload("plugins"))
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
        return Query(cls).from_statement(text(QUERIES["instances-all"]))

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

    def add_group(self, group):
        return InstanceGroups.insert(self, group)

    def enable_plugin(self, plugin):
        return Plugins.insert(self, plugin)


class Groups(Model):
    __tablename__ = "groups"
    __table_args__ = (
        schema.PrimaryKeyConstraint("group_name", "group_kind"),
        {"schema": "application"},
    )

    group_name = Column(types.UnicodeText)
    group_kind = Column(types.UnicodeText)
    group_description = Column(types.UnicodeText)

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

    def asdict(self):
        d = dict(
            name=self.group_name,
            kind=self.group_kind,
            description=self.group_description,
        )
        if self.group_kind == "instance":
            d["role_groups"] = [ari.role_group_name for ari in self.ari]
        else:
            d["instance_groups"] = [ari.instance_group_name for ari in self.ari]
        return d

    @classmethod
    def get(cls, kind, name):
        return Query(cls).from_statement(
            text(QUERIES["groups-get"]).bindparams(kind=kind, name=name)
        )

    @classmethod
    def all(cls, kind):
        return Query(cls).from_statement(
            text(QUERIES["groups-all"]).bindparams(kind=kind)
        )

    @classmethod
    def insert(cls, kind, name, description):
        return Query(cls).from_statement(
            text(QUERIES["groups-insert"]).bindparams(
                kind=kind, name=name, description=description
            )
        )

    @classmethod
    def delete(cls, kind, name):
        return text(
            """DELETE FROM application.groups WHERE group_kind = :kind AND group_name = :name;"""
        ).bindparams(kind=kind, name=name)
