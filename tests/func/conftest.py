from __future__ import absolute_import

import sys

import pytest

from .test.temboard import build_env_dict, drop_env, init_env
from temboardagent.postgres import Postgres



ENV = {}
PY3 = sys.version_info[0] == 3

text_type = str if PY3 else unicode


@pytest.fixture(autouse=True, scope='session')
def env():
    env = build_env_dict()
    drop_env(env)
    init_env(env)
    ENV.update(env)
    try:
        yield ENV
    finally:
        drop_env(env)


def pgconnect(**kw):
    defaults = dict(
        host=ENV['pg']['socket_dir'], port=ENV['pg']['port'],
        user=ENV['pg']['user'], password=ENV['pg']['password'],
        database='postgres',
    )
    kw = dict(defaults, **kw)
    return Postgres(**kw).connect()
