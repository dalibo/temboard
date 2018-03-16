from __future__ import unicode_literals

import logging
import sys

from temboardagent.routing import add_route
from temboardagent.api_wrapper import api_function_wrapper


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


class Hello(object):
    def __init__(self, app, **kw):
        self.app = app

    def load(self):
        add_route('GET', b'/hello')(get_hello)


class Failing(object):
    def __init__(self, app, **kw):
        assert False, "Plugins fails to load."
