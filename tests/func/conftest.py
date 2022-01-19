import os
import sys

import pytest

if True:  # hack flake8
    sys.path.insert(0, os.path.dirname(__file__))

from test.temboard import build_env_dict, drop_env, init_env
from temboardagent.postgres import Postgres


ENV = {}


@pytest.fixture(autouse=True, scope='session')
def env():
    env = build_env_dict()
    drop_env(env)
    init_env(env)
    ENV.update(env)
    try:
        yield ENV
    finally:
        copy_file_to_stream(env['agent']['log_file'], sys.stderr)
        copy_file_to_stream(env['pg']['log_file'], sys.stderr)
        drop_env(env)


def copy_file_to_stream(path, stream):
    stream.write("\n")
    if not os.path.exists(path):
        stream.write("%s does not exists.\n" % path)
    else:
        with open(path) as fo:
            stream.write("%s:" % path)
            for line in fo:
                stream.write(line)


def pgconnect(**kw):
    defaults = dict(
        host=ENV['pg']['socket_dir'], port=ENV['pg']['port'],
        user=ENV['pg']['user'], password=ENV['pg']['password'],
        database='postgres',
    )
    kw = dict(defaults, **kw)
    return Postgres(**kw).connect()
