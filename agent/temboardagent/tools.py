import errno
import logging
import os
import re
from datetime import datetime
from time import strftime, gmtime
from contextlib import contextmanager

from bottle import HTTPError


logger = logging.getLogger(__name__)


def validate_parameters(values, types):
    """
    Verify that each value of dict 'values' is valid. For doing that, we have
    to loop over all 'types' elements which are tuples: ('values' key,
    validation regexp, if the value item currently checked is a list of thing
    to check).
    If values[key] (or each element of it when it's a list) does not match
    with the regexp then we trow an error.
    """
    for (key, typ, is_list) in types:
        try:
            if type(typ) == bytes and hasattr(typ, 'decode'):
                typ = str(typ.decode('utf-8'))
            if not is_list:
                # If 'typ' is a string, it must be considered as a regexp
                # pattern.
                if type(typ) == str and \
                        re.match(typ, str(values[key])) is None:
                    raise HTTPError(406, "Parameter '%s' is malformed."
                                         % (key))
                if type(typ) != str and isinstance(values[key], type(typ)):
                    raise HTTPError(406, "Parameter '%s' is malformed."
                                         % (key))
            if is_list:
                for value in values[key]:
                    if type(typ) == str and re.match(typ, str(value)) is None:
                        raise HTTPError(406, "Parameter '%s' is malformed."
                                             % (key))
                    if type(typ) != str and typ != type(value):
                        raise HTTPError(406, "Parameter '%s' is malformed."
                                             % (key))
        except HTTPError as e:
            raise e
        except KeyError:
            raise HTTPError(406, "Parameter '%s' not sent." % (key))
        except Exception as e:
            logger.exception(str(e))
            raise HTTPError(500, "Internal error.")


MULTIPLIERS = ['', 'k', 'M', 'G', 'T', 'P']


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


def now():
    """Give the current date and time at GMT, suitable for PostgreSQL."""
    return strftime("%Y-%m-%d %H:%M:%S +0000", gmtime())


def fromisoformat(datestr):
    datetime_part, tz_part = datestr.split('+')
    datestr = datetime_part + '+' + tz_part.replace(':', '')
    return datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S.%f%z")


@contextmanager
def noop_manager(ret=None):
    yield ret
