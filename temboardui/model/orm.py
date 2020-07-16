import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    event,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import (
    case,
    column,
    extract,
    func,
)

from temboardui.model import tables

Model = declarative_base()


def validate_int(value):
    if value is None:
        return
    if isinstance(value, unicode):
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
        func.sum(c.shared_blks_read + c.local_blks_read + c.temp_blks_read) /
        total_measure_interval(c.mesure_interval)
    ).label("total_blks_read")


def total_hit(c):
    return (
        func.sum(c.shared_blks_hit + c.local_blks_hit) /
        total_measure_interval(c.mesure_interval)
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


class Instances(Model):
    __table__ = tables.instances
    groups = relationship(
        InstanceGroups,
        order_by="InstanceGroups.group_name",
        backref="instances",
        cascade="save-update, merge, delete, delete-orphan"
    )

    plugins = relationship(
        Plugins,
        order_by="Plugins.plugin_name",
        backref="instances",
        cascade="save-update, merge, delete, delete-orphan"
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
