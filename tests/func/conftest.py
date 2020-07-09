from __future__ import absolute_import

import sys

import pytest

from .test.temboard import build_env_dict, drop_env, init_env


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
