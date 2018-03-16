from __future__ import unicode_literals

import logging
import sys

from temboardagent.routing import add_route
from temboardagent.api_wrapper import (
    api_function_wrapper,
    api_function_wrapper_pg,
)


logger = logging.getLogger('temboardagent.' + __name__)


def say_hello_world(config, http_context):
    """
    Basic "Hello world" API using HTTP method GET.

    Usage:
    $ export XSESSION=`curl -s -k -X POST --data '{"username":"<user>", "password":"<password>"}' https://localhost:2345/login | sed -E "s/^.+\"([a-f0-9]+)\".+$/\1/"`
    $ curl -s -k -H "X-Session:$XSESSION" "https://localhost:2345/hello" | python -m json.tool
    {
        "content": "Hello World."
    }
    """  # noqa
    return {"content": "Hello World."}


def get_hello(http_context, config=None, sessions=None):
    """
    Parameters:
        http_context: HTTP context containing HTTP paramaters and variables.
        config: Agent configuration.
        sessions: List of current sessions.
    """
    return api_function_wrapper(
        config, http_context, sessions,
        sys.modules[__name__], 'say_hello_world')


def say_hello_world_time(conn, config, http_context):
    """
    "Hello world" API using a PostgreSQL connection.

    Usage:
    $ export XSESSION=`curl -s -k -X POST --data '{"username":"<user>", "password":"<password>"}' https://localhost:2345/login | sed -E "s/^.+\"([a-f0-9]+)\".+$/\1/"`
    $ curl -s -k -H "X-Session:$XSESSION" "https://localhost:2345/hello/time" | python -m json.tool
    {
        "message": "Hello World",
        "time": "2016-09-29 10:19:37.059801+02"
    }
    """  # noqa
    conn.execute("""
SELECT 'Hello World' AS message, NOW() AS time
    """)
    row = list(conn.get_rows())[0]
    return {"message": row['message'], "time": row['time']}


def get_hello_time(http_context, config=None, sessions=None):
    return api_function_wrapper_pg(
        config, http_context, sessions,
        sys.modules[__name__], 'say_hello_world_time')


# Defining a new type to validate 'something'.
T_SOMETHING = br'(^[a-z]{1,100}$)'


def say_hello_something(config, http_context):
    """
    "Hello <something>" using slug

    Usage:
    $ export XSESSION=`curl -s -k -X POST --data '{"username":"<user>", "password":"<password>"}' https://localhost:2345/login | sed -E "s/^.+\"([a-f0-9]+)\".+$/\1/"`
    $ curl -s -k -H "X-Session:$XSESSION" "https://localhost:2345/hello/toto" | python -m json.tool
    {
        "content": "Hello toto"
    }
    """  # noqa
    return {"content": "Hello %s" % (http_context['urlvars'][0])}


def get_hello_something(http_context, config=None, sessions=None):
    return api_function_wrapper(
        config, http_context, sessions,
        sys.modules[__name__], 'say_hello_something')


class Hello(object):
    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        # URI **MUST** be bytes.
        add_route('GET', b'/hello')(get_hello)
        add_route('GET', b'/hello/time')(get_hello_time)
        add_route('GET', b'/hello/'+T_SOMETHING)(get_hello_something)


class Failing(object):
    def __init__(self, app, **kw):
        assert False, "Plugins fails to load."
