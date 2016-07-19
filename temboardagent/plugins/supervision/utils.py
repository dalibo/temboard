# -*- coding: utf-8 -*-
import os
import re
import errno
import logging
from time import strftime, gmtime
from subprocess import Popen, PIPE

def exec_command(command_args, stdinput=None, **kwargs):
    """Run a command and give its output and exit code."""

    kwargs.setdefault("stdout", PIPE)
    kwargs.setdefault("stderr", PIPE)
    kwargs.setdefault("stdin", PIPE)

    try:
        process = Popen(command_args, **kwargs)
    except OSError as e:
        logging.error("Could not run: \"%s\"" % ' '.join(command_args))
        logging.error(e.strerror)
        return None, None, None

    (stdout, stderr) = process.communicate(stdinput)

    return process.returncode, stdout, stderr

def now():
    """Give the current date and time at GMT, suitable for PostgreSQL."""
    return strftime("%Y-%m-%d %H:%M:%S +0000", gmtime())


def which(prog, search_path=None):
    """
    Search for a file in the given list of directories or fallback to PATH.

    Args:
        prog (str): the file to search
        search_path (list): list of directories to search
    Returns:
        the first path found

    Example:

    >>> which('ls') #doctest: +SKIP
    '/bin/ls'
    >>> which('ifconfig') #doctest: +SKIP
    Traceback (most recent call last):
    ...
    OSError: No such file or directory
    >>> which('ifconfig', ['/sbin']) #doctest: +SKIP
    '/sbin/ifconfig'
    """

    env_path = re.split(r':', os.environ['PATH'])
    if search_path is None:
        search_path = env_path
    else:
        search_path += env_path

    for d in search_path:
        path = d + '/' + prog
        if os.path.exists(path):
            return path

    raise OSError(os.strerror(errno.ENOENT))

def get_mount_points():
    fs = []
    (rc, out, err) = exec_command([which('df'), '-k'])
    lines = out.splitlines()
    del lines[0] # remove header
    for line in lines:
        cols = line.split()
        # get rid of rootfs which is redundant on Debian
        if cols[0] == 'rootfs':
            continue
        # output may span multiple line
        if len(cols) >= 6:
            fs.append(cols[5])
        elif len(cols) > 1:
            fs.append(cols[4])
    return fs


def find_mount_point(path, mount_points):
    realpath = os.path.realpath(path)

    if not os.path.exists(realpath):
        return None

    # Get the parent dir when it is not a directory
    if not os.path.isdir(realpath):
        realpath = os.path.dirname(realpath)

    # Walk up parents directory
    while True:
        if realpath in mount_points or realpath == '/':
            return realpath

        realpath = os.path.dirname(realpath)

def check_fqdn(name):
    """
    Check if a hostname is fully qualified, it must only contain
    letters, - and have dots.
    """
    # StackOverflow #11809631
    if re.match(r'(?=^.{4,253}$)(^((?!-)[a-zA-Z0-9-]{1,63}(?<!-)\.)+[a-zA-Z]{2,63}\.?$)', name):
        return True
    else:
        return False


MULTIPLIERS = ['', 'k', 'M', 'G']

def to_bytes(size, unit):
    """
    Convert the given size, expressed in unit, to bytes.

    Args:
        size (int): the size to convert to bytes
        unit (str): the unit this size is in
    Returns:
        the converted size

    Example:

    >>> to_bytes(7890, 'M')
    8273264640
    >>> to_bytes(7890, 'unexistent_unit')
    Traceback (most recent call last):
    ...
    KeyError: 'Invalid unit: unexistent_unit'

    """
    if unit not in MULTIPLIERS:
        raise KeyError("Invalid unit: %s" % unit)
    return size * 1024 ** MULTIPLIERS.index(unit)


def parse_linux_meminfo():
    unit_re = re.compile(r'(\d+) ?(\wB)?')
    mem_values = {}
    with open('/proc/meminfo') as f:
        for line in f.read().split("\n"):
            if ':' not in line:
                continue
            key, value = [part.strip() for part in line.split(':', 1)]
            size, unit = unit_re.match(value).groups()
            size = int(size)
            # convert everything to bytes, if a unit is specified
            if unit:
                size = to_bytes(size, unit[:-1])
            mem_values[key] = size
    return mem_values

