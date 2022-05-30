import logging
import os.path
import subprocess
import sys
from configparser import ConfigParser
from getpass import getuser
from pathlib import Path
from textwrap import dedent

import httpx
import pytest
from queue import Queue
from sh import (
    ErrorReturnCode, TimeoutException,
    env as env_cmd,
    # Use bare sudo instead of contrib to ensure non interactive sudo.
    sudo,
)


from .utils import retry_http


logger = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def alice(agent_auto_configure, agent_env, sudo_pguser):
    """Add user alice to agent."""
    proc = sudo_pguser(
        "temboard-agent-adduser",
        _env=agent_env, _in=Queue(), _bg=True)
    proc.process.stdin.put("alice\n")
    proc.process.stdin.put("S3cret_alice\n")
    proc.process.stdin.put("S3cret_alice\n")  # Confirmation
    proc.wait()


@pytest.fixture(scope='session')
def agent_auto_configure(agent_env, agent_sharedir, postgres, pguser, workdir):
    """
    Configure temBoard agent for the postgres instance.
    """

    auto_configure = agent_sharedir / 'auto_configure.sh'
    logger.info("Calling %s.", auto_configure)
    logfile = workdir / 'var/log/agent-auto-configure.log'
    res = subprocess.run(
        [str(auto_configure)],
        stdin=subprocess.PIPE,
        env=dict(
            agent_env,
            ETCDIR=str(workdir / 'etc/temboard-agent'),
            LOGDIR=str(logfile.parent),
            LOGFILE=str(logfile),
            SYSUSER=pguser,
            VARDIR=str(workdir / 'var/temboard-agent'),
        ),
    )
    try:
        res.check_returncode()
    except Exception:
        sys.stderr.write(logfile.read_text())
        raise

    etcdir = workdir / 'etc/temboard-agent/temboard-tests/'
    extra_etc = etcdir / 'temboard-agent.conf.d/tests-extra.conf'
    extra_etc.write_text(dedent(f"""\
    [logging]
    method = file
    destination = {logfile.parent}/temboard-agent.log
    level = DEBUG
    """))


@pytest.fixture(scope='session')
def agent(agent_auto_configure, agent_env, pguser, sudo_pguser, workdir):
    """
    Run configured temBoard agent.

    The agent is a subprocess of pytest.
    """

    proc = sudo_pguser("temboard-agent", _bg=True)
    assert proc.is_alive()

    client = httpx.Client(
        base_url=f"https://localhost:{agent_env['TEMBOARD_PORT']}",
        verify=False,
    )
    client.agent_command = proc
    for attempt in retry_http():
        with attempt:
            client.get('/')

    yield client

    logger.info("Stopping temBoard agent.")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except TimeoutException:
        logger.info("Killing temBoard agent.")
        proc.kill()
        proc.wait(timeout=5)
    except ErrorReturnCode as e:
        logger.info("temBoard agent exited with code %s.", e.exit_code)


@pytest.fixture(scope='session')
def agent_conf(agent_auto_configure, agent_env) -> ConfigParser:
    """
    Read configure temBoard agent configuration files as a ConfigParser object.
    """

    config = ConfigParser()
    files = [
        agent_env['TEMBOARD_CONFIGFILE'],
        agent_env['TEMBOARD_CONFIGFILE'] + '.d/auto.conf',
    ]
    for file_ in files:
        read_, = config.read(file_)
        assert read_ == file_

    return config


@pytest.fixture(scope='session')
def agent_env(env, fqdn, workdir):
    """
    Generate environment for temBoard agent processes.
    """

    return dict(
        env,
        PGDATABASE='postgres',
        PGHOST=str(workdir / 'run/postgresql'),
        PGPASSWORD='S3cret_postgres',
        PGPORT='55432',
        PGUSER='postgres',
        TEMBOARD_CONFIGFILE=str(
            workdir / 'etc/temboard-agent/temboard-tests/temboard-agent.conf'
        ),
        TEMBOARD_HOSTNAME=fqdn,
        TEMBOARD_LOGGING_LEVEL='DEBUG',
        TEMBOARD_PORT='52345',
    )


@pytest.fixture(scope='session')
def agent_sharedir():
    """
    Search for agent share/ directory.
    """

    candidates = [
        # rpm/deb
        '/usr/share/temboard-agent',
        # pip install
        '/usr/local/share/temboard-agent',
        # development
        'agent/share/',
    ]

    for candidate in candidates:
        if os.path.isdir(candidate):
            logger.info("Using %s.", candidate)
            return Path(candidate)


@pytest.fixture(scope='session')
def sudo_pguser(pguser, agent_env):
    """Return amoffat/sh command to eventually run commands as another user."""
    if pguser == getuser():
        # Use /bin/env as a noop.
        cmd = env_cmd
    else:
        cmd = sudo.bake(
            non_interactive=True, set_home=True, preserve_env=True,
            user=pguser,
            _in=None,
        )
        cmd = cmd.bake("env")

    return cmd.bake(f"PATH={os.environ['PATH']}", _env=agent_env)
