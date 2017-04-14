"""
"Hello World" plugin intended to illustrate howto to implement a new API.
WARNING: This plugin is for developer use *ONLY* and shoudn't be loaded.
"""

import sys
from temboardagent.routing import add_route
from temboardagent.api_wrapper import (
    api_function_wrapper,
    api_function_wrapper_pg,
)
from temboardagent.tools import validate_parameters
from temboardagent.errors import HTTPError


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


@add_route('GET', '/hello')
def get_hello(http_context,
              queue_in=None,
              config=None,
              sessions=None,
              commands=None):
    """
    Parameters:
        http_context: HTTP context containing HTTP paramaters and variables.
        queue_in: Task queue to schedule asynchronous job.
        config: Agent configuration.
        sessions: List of current sessions.
        commands: List of current commands (async. jobs).
    """
    return api_function_wrapper(config,
                                http_context,
                                sessions,
                                sys.modules[__name__],
                                'say_hello_world')


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


@add_route('GET', '/hello/time')
def get_hello_time(http_context,
                   queue_in=None,
                   config=None,
                   sessions=None,
                   commands=None):
    return api_function_wrapper_pg(config,
                                   http_context,
                                   sessions,
                                   sys.modules[__name__],
                                   'say_hello_world_time')


# Defining a new type to validate 'something'.
T_SOMETHING = r'(^[a-z]{1,100}$)'


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


@add_route('GET', '/hello/'+T_SOMETHING)
def get_hello_something(http_context,
                        queue_in=None,
                        config=None,
                        sessions=None,
                        commands=None):
    return api_function_wrapper(config,
                                http_context,
                                sessions,
                                sys.modules[__name__],
                                'say_hello_something')


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


@add_route('GET', '/hello2/say')
def get_hello_something2(http_context,
                         queue_in=None,
                         config=None,
                         sessions=None,
                         commands=None):
    return api_function_wrapper(config,
                                http_context,
                                sessions,
                                sys.modules[__name__],
                                'say_hello_something2')


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


@add_route('POST', '/hello3/say')
def get_hello_something3(http_context,
                         queue_in=None,
                         config=None,
                         sessions=None,
                         commands=None):
    return api_function_wrapper(config,
                                http_context,
                                sessions,
                                sys.modules[__name__],
                                'say_hello_something3')


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
    from temboardagent.command import exec_command, oneline_cmd_to_array
    (return_code, stdout, stderr) = exec_command(
                                        oneline_cmd_to_array(
                                            "echo 'Hello %s'" %
                                            http_context['urlvars'][0]
                                            )
                                        )
    return {"content": stdout[:-1]}


@add_route('GET', '/hello4/'+T_SOMETHING)
def get_hello_something4(http_context,
                         queue_in=None,
                         config=None,
                         sessions=None,
                         commands=None):
    return api_function_wrapper(config,
                                http_context,
                                sessions,
                                sys.modules[__name__],
                                'say_hello_something4')
