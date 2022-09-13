# coding: utf-8

import json
from datetime import datetime
try:
    from datetime import timezone
    UTC = timezone.utc
except ImportError:  # PY2
    UTC = None

from .pycompat import IterableUserDict


_UNDEFINED = object()


def dict_factory(iterable=_UNDEFINED, **kw):
    # a dict factory that do not copy.
    if iterable is _UNDEFINED:
        return kw
    elif isinstance(iterable, dict):
        return iterable
    else:
        return dict(iterable, **kw)


class DotDict(IterableUserDict):
    # A wrapper around dict that allows read and write through dot style
    # accessors.

    def __init__(self, *a, **kw):
        self.__dict__['data'] = dict_factory(*a, **kw)

    def __getattr__(self, name):
        try:
            value = self[name]
            # Lazy recursion of DotDict
            if isinstance(value, dict):
                self[name] = value = DotDict(value)
            return value
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            self.__dict__[name] = value  # PY2, use __setattr__
        else:
            if hasattr(value, 'items'):
                value = DotDict(value)
            self[name] = value

    def __setstate__(self, state):
        self.__dict__.update(state)

    def setdefault(self, name, default):
        if hasattr(default, 'items'):
            default = DotDict(default)
        return IterableUserDict.setdefault(self, name, default)


def ensure_bytes(value, encoding='utf-8'):
    if not hasattr(value, "lower"):
        value = str(value)
    if hasattr(value, "isdecimal"):
        return value.encode(encoding)
    return value


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return obj.decode("utf-8")
        else:
            return super(JSONEncoder, self).default(obj)


def utcnow():
    # TZ aware UTC now. Except on Python2.
    return datetime.utcnow().replace(tzinfo=UTC)
