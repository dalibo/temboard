# User Input Validator
#
# These functions provide stateless validation of user input, mainly CLI
# arguments and environment variables.
#
# On invalid input, a ValueError is raised. Other exceptions are considered a
# bug.
#
# A validator is idempotent. It must accepts what it returns.

import json
import logging
import os.path
import re
from distutils.util import strtobool
from logging.handlers import SysLogHandler

from .log import HANDLERS as LOG_METHODS


_address_re = re.compile(
    r'(?:[3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}|\d)'
    r'(\.(?:[3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}|\d'
    r')){3}$'
)


def address(raw):
    if not _address_re.match(raw):
        raise ValueError('invalid address')
    return raw


def boolean(raw):
    if raw in (True, False):
        return raw

    return bool(strtobool(raw))


def dir_(raw):
    raw = os.path.realpath(raw)
    if not os.path.isdir(raw):
        raise ValueError('Not a directory')
    return raw


def file_(raw):
    if not raw:
        return raw
    raw = os.path.realpath(raw)
    if not os.path.exists(raw):
        raise ValueError('%s: File not found' % raw)
    return raw


_identifier_re = re.compile(r'^[a-zA-Z0-9]+$')


def jsonlist(raw):
    if hasattr(raw, 'lower'):
        raw = json.loads(raw)

    if not isinstance(raw, list):
        raise ValueError('not a list')

    raw = [str(e) for e in raw]
    for entry in raw:
        if not _identifier_re.match(entry):
            raise ValueError('%s is invalid' % entry)

    return raw


def port(raw):
    port = int(raw)

    if 0 > port or port > 65635:
        raise ValueError('Port out of range')

    return port


def loglevel(raw):
    raw = raw.upper()
    levelnames = list()
    if hasattr(logging, '_levelNames'):  # pragma: nocover_py3
        levelnames = logging._levelNames
    elif hasattr(logging, '_nameToLevel'):  # pragma: nocover_py2
        levelnames = logging._nameToLevel
    if raw not in levelnames:
        raise ValueError('unkown log level')
    return raw


def logmethod(raw):
    if raw not in LOG_METHODS:
        raise ValueError('unknown logging method %s' % (raw,))
    return raw


def syslogfacility(raw):
    if raw not in SysLogHandler.facility_names:
        raise ValueError('unkown syslog facility')
    return raw


def writeabledir(raw):
    raw = dir_(raw)
    if not os.access(raw, os.W_OK):
        raise ValueError('Not writable')
    return raw


def commalist(raw):
    return list(filter(None, [w.strip() for w in raw.split(',')]))


def quoted(raw):
    for char in ['"', '\'']:
        if raw.startswith(char) and raw.endswith(char):
            raw = raw[1:-1]
    return raw


def nday(raw):
    nday = int(raw)

    if nday < 1:
        raise ValueError('Number of day not valid')

    return nday
