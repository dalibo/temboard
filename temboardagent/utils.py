from UserDict import UserDict


_UNDEFINED = object()


def dict_factory(iterable=_UNDEFINED, **kw):
    # a dict factory that do not copy.
    if iterable is _UNDEFINED:
        return kw
    elif isinstance(iterable, dict):
        return iterable
    else:
        return dict(iterable, **kw)


class DotDict(UserDict):
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
        if hasattr(value, 'items'):
            value = DotDict(value)
        self[name] = value

    def setdefault(self, name, default):
        if hasattr(default, 'items'):
            default = DotDict(default)
        return UserDict.setdefault(self, name, default)

    def __iter__(self):
        return iter(self.keys())
