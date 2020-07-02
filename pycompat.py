# flake8: noqa
# pytype: disable=import-error

import sys


PY3 = sys.version_info > (3,)
PY2 = not PY3

if PY2:
    import ConfigParser as configparser
    from UserDict import IterableUserDict
    from logutils.dictconfig import dictConfig
    from Queue import Empty
else:
    import configparser
    from collections import UserDict as IterableUserDict
    from logging.config import dictConfig
    from queue import Empty
