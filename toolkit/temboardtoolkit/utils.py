import json
from collections import UserDict
from datetime import datetime, timezone

_UNDEFINED = object()


def dict_factory(iterable=_UNDEFINED, **kw):
    # a dict factory that do not copy.
    if iterable is _UNDEFINED:
        return kw
    elif isinstance(iterable, dict):
        return iterable
    else:
        return dict(iterable, **kw)


def strtobool(value):
    if not value:
        return False
    value = str(value).lower()
    if value in ("y", "yes", "t", "true", "on", "1"):
        return True
    if value in ("n", "no", "f", "false", "off", "0"):
        return False
    raise ValueError("invalid truth value %s" % value)


class DotDict(UserDict):
    # A wrapper around dict that allows read and write through dot style
    # accessors.

    def __init__(self, *a, **kw):
        # don't call super()__init__ to avoid RecursionError
        self.__dict__["data"] = dict_factory(*a, **kw)

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
        # only public property are in the dictionnary
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            if hasattr(value, "items"):
                value = DotDict(value)
            self[name] = value

    def __setstate__(self, state):
        self.__dict__.update(state)

    def setdefault(self, name, default):
        if hasattr(default, "items"):
            default = DotDict(default)
        return UserDict.setdefault(self, name, default)


def ensure_bytes(value, encoding="utf-8"):
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
            return super().default(obj)


def utcnow():
    # TZ aware UTC now.
    return datetime.utcnow().replace(tzinfo=timezone.utc)
