# coding: utf-8

import ctypes
import logging
import sys

libc = ctypes.CDLL('libc.so.6')


logger = logging.getLogger(__name__)


def compute_main_module_name(mod):
    # Fix __main__ module to find its importable name.

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


class ProcTitleManager(object):
    def __init__(self, prefix):
        self.prefix = prefix
        self.address = self.size = None

    def setup(self):
        self.address, self.size = get_argv_memory()
        logger.debug(
            "argv is at %#x, len=%d.",
            ctypes.addressof(self.address), self.size)

    def settitle(self, title):
        # cf. https://chromium.googlesource.com/infra/infra/+/69eb0279c12bcede5937ce9298020dd4581e38dd%5E!/
        title = self.prefix + title
        title = title.encode('utf-8')
        # Truncate title to fit in argv memory segment.
        title = title[:self.size - 1]
        # Pad argv with NULL
        title = title.ljust(self.size, b'\0')
        # Overwrite argv segment with proc title
        libc.memcpy(self.address, title, self.size)

    def __call__(self, title):
        return self.settitle(title)
