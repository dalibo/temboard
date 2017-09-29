import logging
import os.path
from distutils.util import strtobool
from logging.handlers import SysLogHandler

from .log import HANDLERS as LOG_METHODS


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


def loglevel(raw):
    raw = raw.upper()
    if raw not in logging._levelNames:
        raise ValueError('unkown log level')
    return raw


def logmethod(raw):
    if raw not in LOG_METHODS:
        raise ValueError('unkown method')
    return raw


def syslogfacility(raw):
    if raw not in SysLogHandler.facility_names:
        raise ValueError('unkown syslog facility')
    return raw
