from __future__ import unicode_literals

import logging
import sys

from temboardagent.routing import add_route
from temboardagent.api_wrapper import (
    api_function_wrapper,
    api_function_wrapper_pg,
)
from temboardagent.command import exec_command
from temboardagent.tools import validate_parameters
from temboardagent.errors import HTTPError


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


def say_hello_something2(config, http_context):
    """
    "Hello <something>" using GET variable.

    Usage:
    $ export XSESSION=`curl -s -k -X POST --data '{"username":"<user>", "password":"<password>"}' https://localhost:2345/login | sed -E "s/^.+\"([a-f0-9]+)\".+$/\1/"`
    $ curl -s -k -H "X-Session:$XSESSION" "https://localhost:2345/hello2/say?something=toto" | python -m json.tool
    {
        "content": "Hello toto"
    }
    """  # noqa
    if http_context and 'something' in http_context['query']:
        validate_parameters(http_context['query'], [
            ('something', T_SOMETHING, True)
        ])
        something = http_context['query']['something'][0]
        return {"content": "Hello %s" % (something)}
    else:
        raise HTTPError(444, "Parameter 'something' not sent.")


def get_hello_something2(http_context, config=None, sessions=None):
    return api_function_wrapper(
        config, http_context, sessions,
        sys.modules[__name__], 'say_hello_something2')


def say_hello_something3(config, http_context):
    """
    "Hello <something>" using POST variable.

    Usage:
    $ export XSESSION=`curl -s -k -X POST --data '{"username":"<user>", "password":"<password>"}' https://localhost:2345/login | sed -E "s/^.+\"([a-f0-9]+)\".+$/\1/"`
    $ curl -s -k -H "X-Session:$XSESSION" -X POST --data '{"something": "toto"}' "https://localhost:2345/hello3/say" | python -m json.tool
    {
        "content": "Hello toto"
    }
    """  # noqa
    if http_context and 'something' in http_context['post']:
        validate_parameters(http_context['post'], [
            ('something', T_SOMETHING, True)
        ])
        something = http_context['post']['something']
        return {"content": "Hello %s" % (something)}
    else:
        raise HTTPError(444, "Parameter 'something' not sent.")


def get_hello_something3(http_context, config=None, sessions=None):
    return api_function_wrapper(
        config, http_context, sessions,
        sys.modules[__name__], 'say_hello_something3')


def say_hello_something4(config, http_context):
    """
    "Hello <something>" using slug & exec_command.

    Usage:
    $ export XSESSION=`curl -s -k -X POST --data '{"username":"<user>", "password":"<password>"}' https://localhost:2345/login | sed -E "s/^.+\"([a-f0-9]+)\".+$/\1/"`
    $ curl -s -k -H "X-Session:$XSESSION" "https://localhost:2345/hello4/toto" | python -m json.tool
    {
        "content": "Hello toto"
    }
    """  # noqa
    (return_code, stdout, stderr) = exec_command([
        'echo', 'Hello', http_context['urlvars'][0],
    ])
    return {"content": stdout[:-1]}


def get_hello_something4(http_context, config=None, sessions=None):
    return api_function_wrapper(
        config, http_context, sessions,
        sys.modules[__name__], 'say_hello_something4')


class Hello(object):
    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        # URI **MUST** be bytes.
        add_route('GET', b'/hello')(get_hello)
        add_route('GET', b'/hello/time')(get_hello_time)
        add_route('GET', b'/hello/'+T_SOMETHING)(get_hello_something)
        add_route('GET', b'/hello2/say')(get_hello_something2)
        add_route('POST', b'/hello3/say')(get_hello_something3)
        add_route('GET', b'/hello4/'+T_SOMETHING)(get_hello_something4)


class Failing(object):
    def __init__(self, app, **kw):
        assert False, "Plugins fails to load."
