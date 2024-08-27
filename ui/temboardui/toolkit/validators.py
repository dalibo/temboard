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
from logging.handlers import SysLogHandler
from urllib.parse import urlparse

from .log import HANDLERS as LOG_METHODS
from .utils import strtobool

_address_re = re.compile(
    r"(?:[3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}|\d)"
    r"(\.(?:[3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}|\d"
    r")){3}$"
)


def address(raw):
    if not _address_re.match(raw):
        raise ValueError("invalid address")
    return raw


def boolean(raw):
    if raw in (True, False):
        return raw

    return strtobool(raw)


def dir_(raw):
    raw = os.path.realpath(raw)
    if not os.path.isdir(raw):
        raise ValueError("Not a directory")
    return raw


_email_re = re.compile(r"^([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)$")


def email(raw):
    if not _email_re.match(raw):
        raise ValueError("invalid email")
    return raw


def file_(raw):
    if not raw:
        return raw
    raw = os.path.realpath(raw)
    if not os.path.exists(raw):
        raise ValueError("%s: File not found" % raw)
    return raw


def password(raw):
    if len(raw) < 8:
        raise ValueError("Password must be at least 8 characters long")
    return raw


def path(raw):
    if not raw:
        return raw
    raw = os.path.realpath(raw)
    parent = os.path.dirname(raw)
    if not os.path.isdir(parent):
        raise ValueError("Missing parent directory of: %s" % raw)
    return raw


def phone(raw):
    if not re.match(r"\+[0-9]+", raw):
        raise ValueError("invalid phone number")
    return raw


def fqdn(raw):
    if "\n" in raw:
        raise ValueError("New line in FQDN.")
    if not re.match(
        r"(?=^.{1,253}$)"  # check length between 4 and 253
        r"(^((?!-)[a-zA-Z0-9-]{1,63}(?<!-))"
        r"(\.(?!-)[a-zA-Z0-9-]{1,63}(?<!-))*$)",
        raw,
    ):
        raise ValueError("%s is not an FQDN" % raw)
    return raw


_identifier_re = re.compile(r"^[a-zA-Z0-9]+$")


def jsonlist(raw):
    if hasattr(raw, "lower"):
        raw = json.loads(raw)

    if not isinstance(raw, list):
        raise ValueError("not a list")

    raw = [str(e) for e in raw]
    for entry in raw:
        if not _identifier_re.match(entry):
            raise ValueError("%s is invalid" % entry)

    return raw


def port(raw):
    port = int(raw)

    if 0 > port or port > 65635:
        raise ValueError("Port out of range")

    return port


def loglevel(raw):
    raw = raw.upper()
    levelnames = logging._nameToLevel
    if raw not in levelnames:
        raise ValueError("unkown log level")
    return raw


def logmethod(raw):
    if raw not in LOG_METHODS:
        raise ValueError(f"unknown logging method {raw}")
    return raw


def syslogfacility(raw):
    if raw not in SysLogHandler.facility_names:
        raise ValueError("unkown syslog facility")
    return raw


def writeabledir(raw):
    raw = dir_(raw)
    if not os.access(raw, os.W_OK):
        raise ValueError("Not writable")
    return raw


def commalist(raw):
    return list(filter(None, [w.strip() for w in raw.split(",")]))


def nday(raw):
    nday = int(raw)

    if nday < 1:
        raise ValueError("Number of day not valid")

    return nday


def url(raw):
    url = urlparse(raw)
    if not url.scheme.startswith("http"):
        raise ValueError("HTTP URL required")
    if not url.netloc:
        raise ValueError("Missing host and port")
    return raw


def slug(raw):
    if not re.match(r"^[a-z0-9_\-.]{3,24}$", raw):
        raise ValueError(
            "identifier must be 3-24 characters long, lowercase or numbers, and may contain point, hyphen or underscore"
        )
    return raw
