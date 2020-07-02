# coding: utf-8
#
# This is a pure python implementation of process title edition
#
# It is based on https://github.com/dvarrazzo/py-setproctitle which contains
# codes from Postgres itself. Postgres as a good experience one editing process
# title on various plateform. However, it's in C.
#
# There is not a single portable way accross OS, Python version and even ps
# implementation.
#
# The simplest and most portable implemention is argv overwriting. Each process
# is initialized with a memory chunk containing, in order : argv, argc,
# environ. This is what appears in /proc/self/cmdline and /proc/self/environ.
#
# Finding the actual address and size of argv is tricky. Once the memory chunk
# is located, we can just write process title in it and pad it with \0.

from __future__ import print_function

import ctypes
import logging
import sys
import os

from .pycompat import PY3


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
    # CPython alters argv in sys.argv. This breaks searching for sys.argv in
    # memory. This function reverses CPython alteration to libc original argv.
    #
    # Alterations are: adding a -c argument, trimming of main module name.

    # We'll loop over a copy of argv. On Python2, we'll insert a new element in
    # argv, offsetting following elements compared to sys.argv. Track this
    # offset here.
    offset = 0
    modname = None
    for i, arg in enumerate(argv[:]):
        if 0 == i:
            # Python interpreter. Skip it.
            continue
        elif not arg.startswith('-'):
            # Python argument. Next argv items are scripts arguments. Stop now.
            break
        elif '-c' == arg:
            # Remove -c from Python args.
            argv[offset+i:offset+i+1] = []
        elif '-m' == arg and modname is None:
            # Restore main module name.
            modname = compute_main_module_name(sys.modules['__main__'])
            if PY3:  # pragma: nocover_py2
                # In PY3, -m module is replaced with -m -m.
                argv[i+1:i+2] = [modname]
            else:  # pragma: nocover_py3
                argv.insert(i + 1, modname)
                # new argv have one more element than Python argv.
                offset += 1

    return argv


def find_argv_memory_from_pythonapi():  # pragma: nocover
    """ Return pointer and size of argv memory segment. """
    # This implemententation works only on Python2. cf.
    # http://docs.cherrypy.org/en/latest/_modules/cherrypy/process/wspbus.html

    # Allocate variable to point to argv
    argv_type = ctypes.c_wchar_p if PY3 else ctypes.c_char_p
    argv = ctypes.POINTER(argv_type)()
    argc = ctypes.c_int()

    # Get them from CPython API.
    ctypes.pythonapi.Py_GetArgcArgv(ctypes.byref(argc), ctypes.byref(argv))

    argl = [argv[i] for i in range(argc.value)]
    fix_argv(argl)

    # Point to first entry of argv.
    address = ctypes.addressof(argv.contents)
    # Compute memory segment size, including all NULLs.
    size = sum(len(arg) for arg in argl) + argc.value

    return argl, address, size


def read_byte(address):
    type_ = ctypes.POINTER(ctypes.c_char)
    return ctypes.cast(address, type_).contents.value[0]


def reverse_walk_memory(address, limit=8192):
    pos = address
    for i in range(limit):
        pos = address - i
        yield pos, read_byte(pos)


def reverse_find_nulstring(walker):
    # Search backward null-terminated strings.
    string = ''
    null = 0 if PY3 else '\x00'
    for addr, b in walker:
        if null == b:
            if string:
                yield addr + 1, string
            string = ''
        else:
            c = chr(b) if PY3 else b
            string = c + string


def find_stack_segment_from_maps(lines):
    for line in lines:
        if not line.endswith('[stack]\n'):
            continue
        # See proc(3) for a description of /proc/self/maps format.
        segment = line.split()
        address_range = segment[0]
        start, end = address_range.split('-')
        return int(start, base=16), int(end, base=16)
    else:
        raise Exception("Can't find stack segment")


def find_argv_memory_from_maps(maps, argv, environ=os.environ):
    stack_start, stack_end = find_stack_segment_from_maps(maps)
    argv = argv[:]
    # Stack ends with argv, environ and a single path. These are all null
    # terminated strings.
    found_environ = False
    walker = reverse_walk_memory(stack_end - 1, limit=stack_end - stack_start)
    for address, string in reverse_find_nulstring(walker):
        # Check if string is an entry from environ list.
        name, _, _ = string.partition('=')
        if name in environ:
            found_environ = True
            continue
        elif not found_environ:
            # We are after environ, just skip until we find an env var
            # declaration.
            continue
        elif string == argv[-1]:
            argv.pop()
            if not argv:
                # Ok we found all args!
                return address
        else:
            raise Exception("Can't find argv in stack segment")


class ProcTitleManager(object):
    def __init__(self, prefix):
        self.prefix = prefix
        self.address = self.size = None

    def setup(self):  # pragma: nocover
        try:
            argv, self.address, self.size = find_argv_memory_from_pythonapi()
            if sys.version_info > (2,):  # pragma: nocover_py2
                # On CPython3, PythonAPI returns a copy of argv. Find argv
                # address from /proc/self/maps.
                with open('/proc/self/maps') as fo:
                    self.address = find_argv_memory_from_maps(
                        argv=argv, maps=fo)
            logger.debug("argv is at %#x, len=%d.", self.address, self.size)
        except Exception as e:
            self.address = self.size = False
            logger.debug("Failed to find argv memory segment: %s", e)

    def settitle(self, title):
        if not self.address:
            return

        # cf. https://dali.bo/tYIql
        title = self.prefix + title
        title = title.encode('utf-8')
        # Truncate title to fit in argv memory segment.
        title = title[:self.size - 1]
        # Pad title with NULL
        title = title.ljust(self.size, b'\0')
        # Overwrite argv segment with proc title
        dest = ctypes.create_string_buffer(title)
        ctypes.memmove(self.address, dest, self.size)
        return title

    def __call__(self, title):
        return self.settitle(title)


if '__main__' == __name__:  # pragma: nocover
    logging.basicConfig(level=logging.DEBUG)
    setproctitle = ProcTitleManager(prefix='temboard-process: ')
    setproctitle.setup()
    setproctitle('test process')
    with open('/proc/self/cmdline') as fo:
        cmdline = fo.read()
    logger.debug('/proc/self/cmdline is %r', cmdline)
    wanted = 'temboard-process: test process'
    assert wanted in cmdline

    if os.environ.get('WAIT'):
        logger.debug("Process title should be %r", wanted)
        print("Hit RET to terminate.", file=sys.stderr, end='')
        if PY3:
            input()
        else:
            raw_input()

    logger.info("OK")
