from sh import temboard_agent


def test_version():
    out = temboard_agent('--version')
    assert 'agent' in out
    assert 'libpq' in out


def test_help():
    assert 'serve' in temboard_agent('--help')


def test_auto_configure(agent_auto_configure, agent_conf):
    assert 'temboard' in agent_conf


def test_route(agent_auto_configure, sudo_pguser):
    out = sudo_pguser('temboard-agent', 'routes')
    assert '/discover' in out


def test_register_command_help(agent_auto_configure, sudo_pguser):
    sudo_pguser("temboard-agent", "register", "--help")


def test_runtask(agent_auto_configure, sudo_pguser):
    out = sudo_pguser('temboard-agent', "runtask", "?")
    assert 'vacuum_worker' in out


def test_start(agent):
    res = agent.get('/')
    assert 404 == res.status_code


def test_proctitle(agent):
    if b'sudo' in agent.proc.cmd[0]:  # CI case
        ppid = agent.proc.pid
        with open(f"/proc/{ppid}/task/{ppid}/children") as fo:
            pid = int(fo.read())
    else:  # dev case
        pid = agent.proc.pid

    with open(f"/proc/{pid}/cmdline") as fo:
        cmdline = fo.read()

    assert cmdline.startswith('temboard-agent: temboard-tests: web')

    with open(f"/proc/{pid}/task/{pid}/children") as fo:
        children = fo.read()
    children = children.split()

    for childpid in children:
        with open(f"/proc/{childpid}/cmdline") as fo:
            cmdline = fo.read()

        assert cmdline.startswith('temboard-agent: temboard-tests: ')

        assert ': worker' in cmdline or ': scheduler' in cmdline


def test_discover(agent, agent_env, pg_version):
    res = agent.get('/discover')
    res.raise_for_status()
    discover = res.json()

    assert pg_version in discover['postgres']['version']
    assert int(agent_env['PGPORT']) == discover['postgres']['port']


def test_status(agent, agent_env, pg_version):
    res = agent.get('/status')
    status = res.json()

    assert 'start_datetime' in status
