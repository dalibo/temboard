# Various functions to expose components version

import ctypes
import re


def read_distinfo():  # pragma: nocover
    with open('/etc/os-release') as fo:
        distinfos = parse_lsb_release(fo)
    return distinfos


def parse_lsb_release(lines):
    _assignement_re = re.compile(
        r"""(?P<variable>[A-Z_]+)="(?P<value>[^"]+)"$"""
    )
    infos = dict()
    for line in lines:
        m = _assignement_re.match(line)
        if not m:
            continue
        infos[m.group('variable')] = m.group('value')
    return infos


def read_libpq_version():
    # Search libpq version bound to this process.

    try:
        # For psycopg2 2.7+
        from psycopg2.extensions import libpq_version
        return libpq_version()
    except ImportError:
        __import__('psycopg2')

        # Search for libpq.so path in loaded libraries.
        with open('/proc/self/maps') as fo:
            for line in fo:
                values = line.split()
                path = values[-1]
                if '/libpq' in path:
                    break
            else:  # pragma: nocover
                raise Exception("libpq.so not loaded")

        libpq = ctypes.cdll.LoadLibrary(path)
        return libpq.PQlibVersion()


def format_pq_version(version):
    pqnums = [
        version / 10000,
        version % 100,
    ]
    if version <= 100000:
        pqnums[1:1] = [(version % 10000) / 100]
    return '.'.join(str(int(n)) for n in pqnums)
