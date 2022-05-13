import json

from sh import temboard_agent, ErrorReturnCode
import pytest


def test_help_version():
    out = temboard_agent('--version')
    assert 'agent' in out
    assert 'libpq' in out

    out = temboard_agent('--help')
    assert 'serve' in out


def test_auto_configure(agent_auto_configure, agent_conf):
    assert 'temboard' in agent_conf


def test_start(agent, agent_conf):
    res = agent.get('/')
    assert 404 == res.status_code


def test_discover(agent, agent_env, pg_version):
    res = agent.get('/discover')
    discover = res.json()

    assert pg_version in discover['pg_version']
    assert int(agent_env['PGPORT']) == discover['pg_port']


def test_temboard_client(agent):
    # Import once debian virtualenv is active.
    from sh import python3

    client = python3.bake("-m", "temboardui.temboardclient", _tty_in=True)

    # Error
    url = f"{agent.base_url}/bad-path"
    with pytest.raises(ErrorReturnCode):
        client(url)

    # GET
    url = f"{agent.base_url}/discover"
    out = client(url)
    data = json.loads(str(out))
    assert 'hostname' in data


def test_runtask(agent, agent_env):
    out = temboard_agent("runtask", "?", _env=agent_env)

    assert 'vacuum_worker' in out
