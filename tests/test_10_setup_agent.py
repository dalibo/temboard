from sh import temboard_agent


def test_version():
    out = temboard_agent('--version')
    assert 'agent' in out
    assert 'libpq' in out


def test_help():
    assert 'serve' in temboard_agent('--help')


def test_route(agent_auto_configure, sudo_pguser, agent_env):
    with sudo_pguser:
        assert '/discover' in temboard_agent('routes', _env=agent_env)


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


def test_register_command_help(agent, agent_env):
    temboard_agent("register", "--help", _env=agent_env)


def test_runtask(agent, agent_env):
    out = temboard_agent("runtask", "?", _env=agent_env)

    assert 'vacuum_worker' in out
