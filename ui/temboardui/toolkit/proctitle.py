# Pure Python procfs-based process title edition
#
#
# This module implements fancy process title in systemctl status or ps output.
# It replaces: `/usr/bin/python3 -m temboardui.main -c
# /etc/temboard/temboard.conf` with `temboard: scheduler` and so on.
#
# There is not a single portable way accross OS, Python version and even ps
# implementation. The simplest and most portable implemention is argv
# overwriting.
#
# CPython API hides original argv. We need to workaround this by searching
# original argv in memory before overwriting this.
#
# Each process is initialized with a memory segment called [stack] containing,
# in order : argv, argc, environ. /proc/self/maps contains the address of the
# stack. This module searches the address of argv in the stack. Once we have
# original argv address and size, we can overwrite the memory with the new
# title.
#
# We truncate title to not overflow argv memory segment. This mean that the
# title maximum length depends on the number of arguments passed to the
# process.
#
# We pad title with null to fill the argv memory segment. This is needed to
# clean end of the title to be displayed in ps output. Otherwise, you'll see
# `temboard: mainon -c /etc/temboard/temboard.conf` instead of `temboard:
# main`, or garbaged from memory.

import ctypes
import logging
import os
import sys

logger = logging.getLogger(__name__)
_setter = None


def set(title):
    return _setter(title)


def init(prefix):
    global _setter
    assert not _setter
    _setter = ProcTitleSetter(prefix)
    _setter.setup()
    set("init")


class ProcTitleSetter:
    def __init__(self, prefix):
        self.prefix = prefix
        # Memory segment containing argv. Will be overriden with new title.
        self.address = None
        # Size of the memory segment containing argv. Will be used to truncate
        # or pad title.
        self.size = None

    def setup(self):  # pragma: nocover
        try:
            # Get argv as defined by the kernel/libc when executing the
            # process. sys.argv does not contains the full argv.
            argv = get_argv_from_pythonapi()
            # Find process stack from /proc/self/maps.
            with open("/proc/self/maps") as fo:
                start, length = find_stack_segment_from_maps(fo)
            argv, self.address = find_argv_in_stack(start, length, argv)
            self.size = carray_size(argv)
            logger.debug("argv is at %#x, len=%d.", self.address, self.size)
        except Exception as e:
            self.address = self.size = False
            logger.debug("Failed to find argv memory segment: %s", e)

    def settitle(self, title):
        if not self.address:
            return

        # cf. https://dali.bo/tYIql
        title = self.prefix + str(title)
        title = title.encode("utf-8")
        # Truncate title to fit in argv memory segment.
        title = title[: self.size - 1]
        # Pad title with NULL bytes to fill the argv segment.
        title = title.ljust(self.size, b"\0")
        # Overwrite argv segment with proc title
        src = ctypes.create_string_buffer(title)
        ctypes.memmove(self.address, src, self.size)
        return title

    def __call__(self, title):
        return self.settitle(title)


def get_argv_from_pythonapi():  # pragma: nocover
    # Wraps CPython API call using ctypes.

    # Allocate variable to point to argv
    arga = ctypes.POINTER(ctypes.c_wchar_p)()
    argc = ctypes.c_int()

    # Get them from CPython API.
    ctypes.pythonapi.Py_GetArgcArgv(ctypes.byref(argc), ctypes.byref(arga))

    # Transform C Array as Python list.
    argv = [arga[i] for i in range(argc.value)]
    return fix_argv(argv)


def find_argv_in_stack(start, length, argv, environ=os.environ):
    # Given an argv list, find the memory segment containing it in
    # /proc/self/maps. This is done by walking backward the stack segment until
    # argv[0] is found. argv[0] is found once the first environment variable is
    # found.
    #
    # stack segment is contains in order argv, argc, environ, and some
    # data irrelevant here.

    argv = argv[:]
    remaining_argv = argv[:]
    found_environ = False
    stackend = start + length - 1
    strings = reverse_find_nulstring(stackend, length)
    for address, string in strings:
        # Check if string is an entry from environ list.
        name, _, _ = string.partition("=")
        if name in environ:
            found_environ = True
            continue
        elif not found_environ:
            # We are after environ, just skip until we find an env var
            # declaration.
            continue
        elif string == remaining_argv[-1]:
            remaining_argv.pop()
            if not remaining_argv:
                # Ok we found all args!
                return argv, address
        elif remaining_argv[-1] == "__COMMAND_STRING__":
            logger.debug("Actual command string: %r.", string)
            remaining_argv.pop()
            command_index = len(remaining_argv)
            argv[command_index] = string
        else:
            raise Exception("Can't find argv in stack segment")


def find_stack_segment_from_maps(lines):
    # See proc(3) for a description of /proc/self/maps format.
    # [stack] is a pseudo path to initial stack segment.
    for line in lines:
        if not line.endswith("[stack]\n"):
            continue
        segment = line.split()
        address_range = segment[0]
        start, end = address_range.split("-")
        start = int(start, base=16)
        end = int(end, base=16)
        return start, end - start
    else:
        raise Exception("Can't find stack segment")


def compute_main_module_name(mod):
    # Fix __main__ module to find its importable name.

    if mod.__name__ == "__main__":
        dir_, file_ = mod.__file__.rsplit("/", 1)
        name = file_.replace(".py", "")
    else:
        name = mod.__name__

    return mod.__package__ + "." + name if mod.__package__ else name


def fix_argv(argv):
    # CPython alters argv. This breaks searching for argv in memory. This
    # function reverses CPython alteration to libc original argv.
    #
    # Alterations are: adding a -c argument, trimming of main module name.
    #
    # Replaces `-c, -c` with `-c __COMMAND_STRING__`.
    # Replaces `-m -m ` with `-m <effective.main.module>`

    modname = None
    # Whether the current -c is placeholder for command string
    command_string = False
    for i, arg in enumerate(argv[:]):
        if 0 == i:
            # Python interpreter. Skip it.
            continue
        elif not arg.startswith("-"):
            # Python argument. Next argv items are scripts arguments. Stop now.
            break
        elif "-" == arg:
            break
        elif "-c" == arg:
            if command_string:
                # Found the second -c, replace it with a placeholder.
                argv[i] = "__COMMAND_STRING__"
                break
            else:
                # Next -c will be a placeholder for actual python online passed
                # as argument to Python
                command_string = True
        elif "-m" == arg and modname is None:
            # Restore main module name.
            modname = compute_main_module_name(sys.modules["__main__"])
            # In PY3, -m module is replaced with -m -m.
            argv[i + 1] = modname
            break

    return argv


def reverse_find_nulstring(address, limit=8192):
    # Search backward null-terminated strings.
    string = ""
    null = 0
    for addr, b in reverse_walk_memory(address, limit):
        if null == b:
            if string:
                yield addr + 1, string
            string = ""
        else:
            string = chr(b) + string


def reverse_walk_memory(address, limit):
    # yields bytes of a memory segment, one by one, in reverse order.
    pos = address
    for i in range(limit):
        pos = address - i
        yield pos, read_byte(pos)


def read_byte(address):
    type_ = ctypes.POINTER(ctypes.c_char)
    return ctypes.cast(address, type_).contents.value[0]


def carray_size(list_):
    return sum(len(s) for s in list_) + len(list_)


def test_main():  # pragma: nocover
    # Test proctitle editing. Set WAIT=1 environ for the process to wait for
    # RET before failing.

    logging.basicConfig(level=logging.DEBUG)
    setproctitle = ProcTitleSetter(prefix="temboard-process: ")
    setproctitle.setup()
    setproctitle("test process")
    with open("/proc/self/cmdline") as fo:
        cmdline = fo.read()
    logger.debug("/proc/self/cmdline is %r", cmdline)
    wanted = "temboard-process: test process"
    if wanted in cmdline:
        logger.info("PASS")
        return 0

    if os.environ.get("WAIT"):
        logger.debug("Process title should be %r", wanted)
        print("Hit RET to terminate.", file=sys.stderr, end="")
        input()

    logger.error("FAIL")
    return 1


if "__main__" == __name__:  # pragma: nocover
    os._exit(test_main())
