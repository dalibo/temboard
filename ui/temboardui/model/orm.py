import datetime
import string
from secrets import choice

from past.builtins import basestring
from sqlalchemy import Boolean, DateTime, Integer, String, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.query import Query
from sqlalchemy.schema import Column
from sqlalchemy.types import TIMESTAMP, BigInteger, UnicodeText

from temboardui.model import tables

from ..toolkit.utils import utcnow
from . import QUERIES

Model = declarative_base()


def validate_int(value):
    if value is None:
        return
    if isinstance(value, str):
        value = int(value)
    if isinstance(value, basestring):
        value = int(value)
    assert isinstance(value, int)
    return value


def validate_string(value):
    assert isinstance(value, basestring)
    return value


def validate_datetime(value):
    assert isinstance(value, datetime.datetime)
    return value


def validate_boolean(value):
    if isinstance(value, int):
        if value == 1:
            value = True
        if value == 0:
            value = False
    if isinstance(value, basestring):
        if (
            str(value).lower() == "yes"
            or str(value).lower() == "true"
            or str(value).lower() == "t"
            or value == "1"
        ):
            value = True
        if (
            str(value).lower() == "no"
            or str(value).lower() == "false"
            or str(value).lower() == "f"
            or value == "0"
        ):
            value = False
    assert isinstance(value, bool)
    return value


validators = {
    Integer: validate_int,
    String: validate_string,
    DateTime: validate_datetime,
    Boolean: validate_boolean,
}


@event.listens_for(Model, "attribute_instrument")
def configure_listener(class_, key, inst):
    if not hasattr(inst.property, "columns"):
        return

    @event.listens_for(inst, "set", retval=True)
    def set_(instance, value, oldvalue, initiator):
        validator = validators.get(inst.property.columns[0].type.__class__)
        if validator:
            try:
                return validator(value)
            except AssertionError:
                raise Exception("%s: wrong type." % (inst.property))
        else:
            return value


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
    __table__ = tables.plugins


class InstanceGroups(Model):
    __table__ = tables.instance_groups


class RoleGroups(Model):
    __table__ = tables.role_groups


class AccessRoleInstance(Model):
    __table__ = tables.access_role_instance


class Roles(Model):
    __table__ = tables.roles
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
    __table__ = tables.instances
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
    __table__ = tables.groups
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
