from __future__ import division
from builtins import str
from past.builtins import basestring
from builtins import object
from past.utils import old_div
import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    event,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.orm.query import Query
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import (
    Column,
)
from sqlalchemy.types import (
    UnicodeText,
    BigInteger,
    TIMESTAMP,
)
from sqlalchemy.sql import (
    case,
    column,
    extract,
    func,
)

from temboardui.model import tables
from . import QUERIES
from ..toolkit.utils import utcnow


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
        if str(value).lower() == 'yes' or \
           str(value).lower() == 'true' or \
           str(value).lower() == 't' or value == '1':
            value = True
        if str(value).lower() == 'no' or \
           str(value).lower() == 'false' or \
           str(value).lower() == 'f' or value == '0':
            value = False
    assert isinstance(value, bool)
    return value


validators = {
    Integer: validate_int,
    String: validate_string,
    DateTime: validate_datetime,
    Boolean: validate_boolean
}


def diff(var):
    return (func.max(column(var)) - func.min(column(var))).label(var)


def to_epoch(column):
    return extract("epoch", column).label(column.name)


def total_measure_interval(column):
    return extract(
        "epoch",
        case([(func.min(column) == '0 second', '1 second')],
             else_=func.min(column)))


# We use 8192 as default value for block size
# Ideally we should get this value from agent
block_size = 8192


def total_read(c):
    return (
        old_div(func.sum(c.shared_blks_read + c.local_blks_read +
                         c.temp_blks_read),
                total_measure_interval(c.mesure_interval))
    ).label("total_blks_read")


def total_hit(c):
    return (
        old_div(func.sum(c.shared_blks_hit + c.local_blks_hit),
                total_measure_interval(c.mesure_interval))
    ).label("total_blks_hit")


@event.listens_for(Model, 'attribute_instrument')
def configure_listener(class_, key, inst):
    if not hasattr(inst.property, 'columns'):
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
    __tablename__ = 'apikeys'
    __table_args__ = {'schema': 'application'}

    id = Column(BigInteger, primary_key=True)
    secret = Column(UnicodeText)
    comment = Column(UnicodeText)
    cdate = Column(TIMESTAMP(timezone=True))
    edate = Column(TIMESTAMP(timezone=True))

    # See
    # https://docs.sqlalchemy.org/en/14/orm/queryguide.html#getting-orm-results-from-textual-and-core-statements

    @classmethod
    def insert(cls, secret, comment):
        return Query(cls).from_statement(
            text(QUERIES['apikeys-insert'])
            .bindparams(secret=secret, comment=comment)
            .columns(*cls.__mapper__.c.values())
        )

    @classmethod
    def select_active(cls):
        return Query(cls).from_statement(
            text(QUERIES['apikeys-select-active'])
            .columns(*cls.__mapper__.c.values())
        )

    @classmethod
    def delete(cls, id):
        return Query(cls).from_statement(
            text(QUERIES['apikeys-delete'])
            .bindparams(id=id)
            .columns(cls.id, cls.comment)
            )

    @classmethod
    def purge(cls):
        return Query(cls).from_statement(
            text(QUERIES['apikeys-purge'])
            .columns(cls.id, cls.comment)
            )

    @classmethod
    def select_secret(cls, secret):
        return Query(cls).from_statement(
            text(QUERIES['apikeys-select-secret'])
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
        cascade="save-update, merge, delete, delete-orphan"
    )


class StubRole(object):
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
        lazy='joined',
    )

    plugins = relationship(
        Plugins,
        order_by="Plugins.plugin_name",
        backref="instances",
        cascade="save-update, merge, delete, delete-orphan",
        lazy='joined',
    )

    def __str__(self):
        return '%s:%s' % (self.hostname, self.pg_port)

    @classmethod
    def factory(
            cls,
            agent_address,
            agent_port,
            discover,
            discover_etag=None,
            agent_key=None,
            notify=False,
            comment=None,
    ):
        return cls(
            agent_address=str(agent_address),
            agent_port=int(agent_port),
            discover=discover,
            discover_etag=discover_etag,
            pg_port=int(discover['postgres']['port']),
            hostname=discover['system']['fqdn'],
            agent_key=agent_key,
            notify=bool(notify),
            comment=comment or '',
        )

    @classmethod
    def get(cls, agent_address, agent_port):
        return (
            Query(cls)
            .prefix_with('-- Instances.get\n')
            .filter(cls.agent_address == str(agent_address))
            .filter(cls.agent_port == int(agent_port))
        )

    # Compatibility from new JSONb discover to old column discover.
    @property
    def cpu(self):
        d = self.discover or {}
        return d.get('system', {}).get('cpu_count')

    @property
    def memory_size(self):
        d = self.discover or {}
        return d.get('system', {}).get('memory')

    @property
    def pg_data(self):
        d = self.discover or {}
        return d.get('postgres', {}).get('data_directory')

    @property
    def pg_version(self):
        d = self.discover or {}
        return d.get('postgres', {}).get('version')

    @property
    def pg_version_summary(self):
        d = self.discover or {}
        return d.get('postgres', {}).get('version_summary')

    def dashboard_url(self, app):
        scheme = 'https' if app.config.temboard.ssl_key_file else 'http'
        host = app.config.temboard.address
        port = app.config.temboard.port
        path = '/server/%s/%s/dashboard' % (
            self.agent_address, self.agent_port)
        return '%s://%s:%s%s' % (scheme, host, port, path)

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
            AccessRoleInstance.instance_group_kind
        ]
    )


class Biggest(object):

    def __init__(self, order_by):
        self.order_by = order_by

    def __call__(self, var, minval=0, label=None):
        label = label or var
        return func.greatest(
            column(var) -
            func.lag(column(var))
            .over(order_by=self.order_by),
            minval
        ).label(label)


class Biggestsum(object):

    def __init__(self, order_by):
        self.order_by = order_by

    def __call__(self, var, minval=0, label=None):
        label = label or var
        return func.greatest(
            func.sum(column(var)) -
            func.lag(func.sum(column(var)))
            .over(order_by=self.order_by),
            minval
        ).label(label)
