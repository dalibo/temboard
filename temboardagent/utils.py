# coding: utf-8

import ctypes
import logging
import sys

try:
    from UserDict import IterableUserDict
except ImportError:
    from collections import UserDict as IterableUserDict


logger = logging.getLogger(__name__)

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
        if hasattr(value, 'items'):
            value = DotDict(value)
        self[name] = value

    def __setstate__(self, state):
        self.__dict__.update(state)

    def setdefault(self, name, default):
        if hasattr(default, 'items'):
            default = DotDict(default)
        return IterableUserDict.setdefault(self, name, default)


libc = ctypes.CDLL('libc.so.6')


def compute_main_module_name(mod):
    # Fix __main__ module to find it's importable name

    if mod.__name__ == '__main__':
        dir_, file_ = mod.__file__.rsplit('/', 1)
        name = file_.replace('.py', '')
    else:
        name = mod.__name__

    return mod.__package__ + '.' + name


def fix_argv(argv):
    # Clean '-c' added by CPython.
    try:
        argv.remove('-c')
    except ValueError:
        pass

    # Search for -m and readd modname
    try:
        m_ind = argv.index('-m')
    except ValueError:
        pass
    else:
        modname = compute_main_module_name(sys.modules['__main__'])
        argv.insert(m_ind + 1, modname)


def get_argv_memory():
    """ Return pointer and size of argv memory segment. """
    # This implemententation works only on Python2. cf.
    # http://docs.cherrypy.org/en/latest/_modules/cherrypy/process/wspbus.html

    # Allocate variable to point to argv
    argv = ctypes.POINTER(ctypes.c_char_p)()
    argc = ctypes.c_int()

    # Get them from CPython API.
    ctypes.pythonapi.Py_GetArgcArgv(ctypes.byref(argc), ctypes.byref(argv))

    argl = [argv[i] for i in range(argc.value)]
    fix_argv(argl)

    address = argv.contents
    # Compute memory segment size, including all NULLs.
    size = sum(len(arg) for arg in argl) + argc.value

    return address, size


def setproctitle(title):
    # cf. https://chromium.googlesource.com/infra/infra/+/69eb0279c12bcede5937ce9298020dd4581e38dd%5E!/
    address, size = get_argv_memory()
    logger.debug("argv is at %#x, len=%d.", ctypes.addressof(address), size)
    title = title.encode('utf-8')
    # Truncate title to fit in argv memory segment.
    title = title[:size - 1]
    # Pad argv with NULL
    title = title.ljust(size, b'\0')
    # Overwrite argv segment with proc title
    libc.memcpy(address, title, size)
