import datetime
from sqlalchemy import (
    Integer,
    String,
    DateTime,
    Boolean,
    event,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

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
