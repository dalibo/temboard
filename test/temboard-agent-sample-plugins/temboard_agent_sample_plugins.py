from __future__ import unicode_literals

import logging
import os
from pickle import dumps as pickle, loads as unpickle

from temboardagent.errors import UserError
from temboardagent.routing import add_route
from temboardagent.command import exec_command
from temboardagent.tools import validate_parameters
from temboardagent.errors import HTTPError
from temboardagent.configuration import OptionSpec
from temboardagent.scheduler import taskmanager


logger = logging.getLogger(__name__)
APP = None


def get_hello(http_context, app):
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


def get_hello_time(http_context, app):
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
    with app.postgres.connect() as conn:
        conn.execute("""SELECT 'Hello World' AS message, NOW() AS time""")
        row = list(conn.get_rows())[0]
    return {"message": row['message'], "time": row['time']}


# Defining a new type to validate 'something'.
T_SOMETHING = br'(^[a-z]{1,100}$)'


def get_hello_pathinfo(http_context, app):
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


def get_hello2_say_query(http_context, config):
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


def post_hello3_say(config, http_context):
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


def get_hello4_exec(config, http_context):
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


def get_hello_from_config(http_context, app):
    """
    "Hello <something>" using configuration.

    Usage:
    $ export XSESSION=`curl -s -k -X POST --data '{"username":"<user>", "password":"<password>"}' https://localhost:2345/login | sed -E "s/^.+\"([a-f0-9]+)\".+$/\1/"`
    $ curl -s -k -H "X-Session:$XSESSION" "https://localhost:2345/hello/from_config" | python -m json.tool
    {
        "content": "Hello toto"
    }
    """  # noqa
    return {"content": "Hello %s!" % app.config.hello.name}


def worker_hello(*a, **kw):
    with APP.postgres.connect() as conn:
        conn.execute("""SELECT 'Hello World' AS message, NOW() AS time;""")
        row = list(conn.get_rows())[0]
    logger.info("Hello from worker.")
    return {"message": row['message'], "time": row['time']}


def get_hello_from_worker(http_context, app):
    """
    "Hello <something>" using configuration.

    Usage:
    $ export XSESSION=`curl -s -k -X POST --data '{"username":"<user>", "password":"<password>"}' https://localhost:2345/login | sed -E "s/^.+\"([a-f0-9]+)\".+$/\1/"`
    $ curl -s -k -H "X-Session:$XSESSION" "https://localhost:2345/hello/from_worker" | python -m json.tool
    {
        "content": "Hello toto"
    }
    """  # noqa
    tm_sock_path = os.path.join(
        app.config.temboard['home'], '.tm.socket').encode('ascii')
    logger.info("Listing tasks.")
    task_list_resp = taskmanager.TaskManager.send_message(
        tm_sock_path,
        taskmanager.Message(taskmanager.MSG_TYPE_TASK_LIST, None),
        authkey=None,
    )
    for task_data in task_list_resp:
        if task_data['worker_name'] == worker_hello.__name__:
            break
    else:
        raise Exception("Worker didn't run")

    return task_data['output']


def hello_task_manager_bootstrap(context):
    try:
        interval = APP.config.hello.background_worker_interval
    except AttributeError as e:
        logger.warn("Unable to get hello config: %s entry does not exists", e)
        logger.warn("Is hellong plugin loaded?")
        return

    yield taskmanager.Task(
        worker_name=worker_hello.__name__,
        id=worker_hello.__name__,
        options={},
        redo_interval=interval,
    )


class Hello(object):
    pg_min_version = 90400
    my_options_specs = [
        OptionSpec('hello', 'name', default='World'),
        OptionSpec(
            'hello', 'background_worker_interval', default=10, validator=int),
    ]

    def __init__(self, app, **kw):
        self.app = app
        self.app.config.add_specs(self.my_options_specs)

    def load(self):
        global APP
        APP = self.app

        pg_version = self.app.postgres.fetch_version()
        if pg_version < self.pg_min_version:
            raise UserError("hellong is incompatible with Postgres below 9.4")

        # URI **MUST** be bytes.
        add_route('GET', b'/hello')(get_hello)
        add_route('GET', b'/hello/time')(get_hello_time)
        add_route('GET', b'/hello/' + T_SOMETHING)(get_hello_pathinfo)
        add_route('GET', b'/hello2/say')(get_hello2_say_query)
        add_route('POST', b'/hello3/say')(post_hello3_say)
        add_route('GET', b'/hello4/' + T_SOMETHING)(get_hello4_exec)
        add_route('GET', b'/hello/from_config')(get_hello_from_config)
        add_route('GET', b'/hello/from_background_worker')(
            get_hello_from_worker)

        taskmanager.worker(pool_size=1)(worker_hello)
        taskmanager.bootstrap()(hello_task_manager_bootstrap)

    def unload(self):
        self.app.config.remove_specs(self.my_options_specs)
        logger.info("Good by from hellong!")


class Failing(object):
    def __init__(self, app, **kw):
        assert False, "Plugins fails to load."
