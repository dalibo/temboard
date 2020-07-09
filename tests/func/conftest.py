from __future__ import absolute_import

import pytest

from .test.temboard import build_env_dict, drop_env, init_env


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
        drop_env(env)
