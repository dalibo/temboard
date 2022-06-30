import sys


PY3 = sys.version_info > (3,)
PY2 = not PY3

if PY2:
    import ConfigParser as configparser
    from UserDict import IterableUserDict
    from Queue import Empty
    from urlparse import urlparse
    from urllib2 import HTTPError
    from urllib import quote_plus
    from cStringIO import StringIO
else:
    import configparser  # noqa: F401
    from collections import UserDict as IterableUserDict  # noqa: F401
    from queue import Empty  # noqa: F401
    from urllib.parse import quote_plus, urlparse  # noqa: F401
    from urllib.error import HTTPError  # noqa: F401
    from io import StringIO  # noqa: F401
