from distutils.util import strtobool
import os.path


def boolean(raw):
    if raw in (True, False):
        return raw

    return bool(strtobool(raw))


def file_(raw):
    raw = os.path.realpath(raw)
    if not os.path.exists(raw):
        raise ValueError('File not found')
    return raw


def port(raw):
    port = int(raw)

    if 0 > port or port > 65635:
        raise ValueError('Port out of range')

    return port
