import pytest

from test.temboard import init_env, drop_env


ENV = {}


@pytest.fixture(autouse=True, scope='session')
def env():
    env = init_env()
    ENV.update(env)
    try:
        yield env
    except Exception:
        raise
    finally:
        drop_env(env)
