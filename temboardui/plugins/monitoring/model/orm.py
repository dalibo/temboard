from temboardui.plugins.monitoring.model import tables

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.inspection import inspect


class ModelMixin(object):
    """
    Class to be mixed in with every mapped class
    """

    @classmethod
    def from_dict(cls, dict_values, recurse=False):
        """
        Build an instance of this model from a dictionary.
        Additional keys are discarded along the way.

        Args:

        dict_values (dict):
            a dictionary from which the instance should be built
        recurse (bool):
            if ``True``, also builds related instances. Else, only the base
            columns are included.
        """
        mapper = inspect(cls)
        columns_values = {
            key: value
            for key, value in dict_values.items()
            if key in mapper.column_attrs
        }
        if recurse:
            for key, relationship_property in mapper.relationships.items():
                target_cls = relationship_property.mapper.class_
                value = dict_values.get(key)
                if isinstance(value, dict):
                    columns_values[key] = target_cls.from_dict(value)
                elif isinstance(value, list):
                    subvalues = columns_values.setdefault(key, [])
                    for val in value:
                        if isinstance(val, dict):
                            subvalues.append(target_cls.from_dict(val))
                        else:
                            subvalues.append(target_cls(val))
        return cls(**columns_values)


Model = declarative_base(cls=(ModelMixin,))


class Host(Model):
    __table__ = tables.hosts

    def __repr__(self):
        return "host: %s" % self.hostname


class Instance(Model):
    __table__ = tables.instances
    host = relationship('Host', backref='instances')

    def __repr__(self):
        return "instance: %s:%s" % (self.host_id, self.port)


class Check(Model):
    __table__ = tables.checks
    host = relationship('Host', backref='checks')
    instance = relationship('Instance', backref='checks')


class CheckState(Model):
    __table__ = tables.checkstates
    check = relationship('Check', backref='states')


class CollectorStatus(Model):
    __table__ = tables.collector_status
    instance = relationship('Instance',
                            backref=backref('collector_statuts',
                                            cascade='all, delete-orphan'))
