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
from sh import (
    ErrorReturnCode,
    TimeoutException,
    # Use bare sudo instead of contrib to ensure non interactive sudo.
    sudo,
)
from sh import env as env_cmd

from .utils import copy_files, retry_http

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def agent_auto_configure(agent_env, agent_sharedir, postgres, pguser, ui_url, workdir):
    """
    Configure temBoard agent for the postgres instance.
    """

    auto_configure = agent_sharedir / "auto_configure.sh"
    etcdir = Path(agent_env["TEMBOARD_CONFIGFILE"]).parent
    logger.info("Calling %s.", auto_configure)
    if "CI" in os.environ:
        logfile = workdir / "var/log/temboard-agent-auto-configure.log"
        logdir = workdir / "var/log/temboard-agent"
        env = dict(agent_env)
    else:
        logfile = workdir / "var/log/agent/auto-configure.log"
        logfile.parent.mkdir()
        logdir = logfile.parent
        env = dict(
            agent_env,
            ETCDIR=str(etcdir.parent),
            LOGDIR=str(logfile.parent),
            LOGFILE=str(logfile),
            SYSUSER=pguser,
            VARDIR=str(workdir / "var/agent"),
        )

    try:
        subprocess.run([auto_configure, ui_url], env=env).check_returncode()
    except Exception:
        sys.stderr.write(logfile.read_text())
        raise

    extra_etc = etcdir / "temboard-agent.conf.d/tests-extra.conf"
    extra_etc.write_text(
        dedent(f"""\
    [logging]
    method = file
    destination = {logdir}/serve.log
    level = DEBUG
    """)
    )

    yield

    logger.info("Purging agent installation.")
    purge = agent_sharedir / "purge.sh"
    try:
        subprocess.run([purge, "temboard-tests"], env=env).check_returncode()
    except Exception:
        sys.stderr.write(logfile.read_text())
        raise


@pytest.fixture(scope="session")
def agent(agent_auto_configure, agent_env, pguser, sudo_pguser, ui, workdir):
    """
    Run configured temBoard agent.

    The agent is a subprocess of pytest.
    """

    sudo_pguser("temboard-agent", "fetch-key", _env=agent_env)

    proc = sudo_pguser(
        "temboard-agent",
        # This --config is redudnant, its only to pad place in cmdline for
        # setproctitle.
        "--config",
        agent_env["TEMBOARD_CONFIGFILE"],
        _bg=True,
    )
    assert proc.is_alive()

    client = httpx.Client(
        base_url=f"https://localhost:{agent_env['TEMBOARD_PORT']}", verify=False
    )
    client.proc = proc
    logger.info("Waiting for agent to come up.")
    for attempt in retry_http():
        with attempt:
            client.get("/")

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

    if "CI" not in os.environ:
        return

    candidates = [
        workdir / "var/log/agent/auto-configure.log",
        workdir / "var/log/agent/serve.log",
        workdir / "var/log/temboard-agent-auto-configure.log",
        workdir / "var/log/temboard-agent/serve.log",
    ]
    copy_files(candidates, Path("tests/logs"))


@pytest.fixture(scope="session")
def agent_conf(agent_auto_configure, agent_env) -> ConfigParser:
    """
    Read configure temBoard agent configuration as a ConfigParser object.
    """

    config = ConfigParser()
    config.read(agent_env["TEMBOARD_CONFIGFILE"])
    return config


@pytest.fixture(scope="session")
def agent_env(env, fqdn, workdir):
    """
    Generate environment for temBoard agent processes.
    """

    dirname = "temboard-agent" if "CI" in os.environ else "agent"
    return dict(
        env,
        PGDATABASE="postgres",
        PGHOST=str(workdir / "run/postgresql"),
        PGPASSWORD="S3cret_postgres",
        PGPORT="55432",
        PGUSER="postgres",
        TEMBOARD_CONFIGFILE=str(
            workdir / "etc" / dirname / "temboard-tests/temboard-agent.conf"
        ),
        TEMBOARD_HOSTNAME=fqdn,
        TEMBOARD_LOGGING_LEVEL="DEBUG",
        TEMBOARD_PORT="52345",
    )


@pytest.fixture(scope="session")
def agent_sharedir():
    """
    Search for agent share/ directory.
    """

    candidates = [
        # rpm/deb
        "/usr/share/temboard-agent",
        # pip install
        "/usr/local/share/temboard-agent",
        # development
        "agent/share/",
    ]

    for candidate in candidates:
        if os.path.isdir(candidate):
            logger.info("Using %s.", candidate)
            return Path(candidate)


@pytest.fixture(scope="session")
def sudo_pguser(pguser, agent_env):
    """Return amoffat/sh command to eventually run commands as another user."""
    if pguser == getuser():
        # Use /bin/env as a noop.
        cmd = env_cmd
    else:
        cmd = sudo.bake(
            non_interactive=True,
            set_home=True,
            preserve_env=True,
            user=pguser,
            _in=None,
        )
        cmd = cmd.bake("env")

    return cmd.bake(f"PATH={os.environ['PATH']}", _env=agent_env)
