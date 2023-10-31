#
# Setup postgres, agent and UI for testing
#
# This file implements deployment of postgres, agent and UI in tests/workdir/
# directory. It uses auto_configure.sh and handles being executed either as
# root or as user.
#
# This file defines custom pytest options. See pytest_addoptions.
#

import logging
import os
import sys
from errno import ENOTEMPTY
from functools import partial
from pathlib import Path

import pytest
import sh
from sh import (
    hostname, temboard, temboard_agent,
)

from fixtures.postgres import POSTGRESQL_AVAILABLE_VERSIONS
from fixtures.utils import rmtree

# Import fixtures
from fixtures import *  # noqa: F401, F403
from fixtures.utils import session_tag, copy_files


logger = logging.getLogger(__name__)


@pytest.fixture(scope='session', autouse=True)
def env():
    """
    Configure environment with superuser privileges.

    This is the environment for auto_configure.sh scripts, etc.
    """

    # Configure libpq with superuser from docker-compose.yml
    os.environ.setdefault('PGHOST', '0.0.0.0')
    os.environ.setdefault('PGPORT', '5432')
    os.environ.setdefault('PGUSER', 'postgres')
    os.environ.setdefault('PGPASSWORD', 'postgres')

    return os.environ


@pytest.fixture(scope='session')
def fqdn():
    """
    Determine host FQDN.
    """
    fqdn = str(hostname('--fqdn')).strip()
    return fqdn if '.' in fqdn else 'localhost.localdomain'


@pytest.fixture(scope='session', autouse=True)
def log_tweaks():
    """
    Send logs to capsys instead of caplog.
    """

    formatter = logging.Formatter(
        fmt="%(asctime)s pytest[%(process)d] %(levelname)s:  "
        "%(module)s: %(message)s"
    )
    formatter.datefmt = '%Y-%m-%d %H:%M:%S %Z'
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    yield

    # Try to remove log directory if empty.
    logdir = Path("tests/logs")
    try:
        if logdir.exists():
            logdir.rmdir()
    except OSError as e:
        if ENOTEMPTY != e.errno:
            raise


@pytest.fixture(autouse=True)
def save_logs(request, workdir):
    yield

    if hasattr(request.node, 'rep_call') and request.node.rep_call.passed:
        return

    logdir = Path("tests/logs") / session_tag / request.node.nodeid
    candidates = [
        workdir / 'var/log/agent/auto-configure.log',
        workdir / 'var/log/agent/serve.log',
        workdir / 'var/log/temboard-agent/serve.log',
        workdir / 'var/log/temboard-auto-configure.log',
        workdir / 'var/log/temboard/serve.log',
        workdir / 'var/log/ui/auto-configure.log',
        workdir / 'var/log/ui/serve.log',
        workdir / 'var/log/postgresql/postgres.log',
    ]

    copy_files(candidates, logdir)


def pytest_addoption(parser):
    POSTGRESQL_AVAILABLE_VERSIONS.search_installed_versions()
    parser.addoption(
        "--pg-version",
        choices=POSTGRESQL_AVAILABLE_VERSIONS.keys(),
        default=POSTGRESQL_AVAILABLE_VERSIONS.most_recent_version,
        help=(
            "Monitor specified PostgreSQL version"
            " (default: %(default)s)"
        ),
    )
    parser.addoption(
        "--selenium",
        default=os.environ.get('SELENIUM', 'http://localhost:4444/wd/hub'),
        help=(
            "URL for remote selenium webdriver"
            " (default: %(default)s). Env var: SELENIUM."
        ),
    )


def pytest_report_header(config):
    pg_version = config.getoption("--pg-version")
    bindir = POSTGRESQL_AVAILABLE_VERSIONS[pg_version]

    versions = {
        "postgresql": f"{pg_version} ({bindir})",
    }

    agent_version = temboard_agent("--version")
    temboard_version = temboard("--version")

    joined_versions = str(temboard_version) + str(agent_version)
    lines = sorted(joined_versions.splitlines())

    for line in lines:
        if 'agent' in line:
            # Replace temBoard agent by temBoard-agent
            line = line.replace(' ', '-', 1)
        component, version = line.split(' ', 1)
        component = component.lower()
        if 'python' == component:
            continue
        versions[component] = version

    return [f"{k}: {v}" for k, v in versions.items()]


# https://docs.pytest.org/en/7.0.x/example/simple.html#making-test-result-information-available-in-fixtures
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(scope='session', autouse=True)
def sh_tweaks(ui_env):
    """
    Tweaks amoffat/sh for testing.
    """

    # amoffat/sh defaults are good for scripting. These tweaks integrates
    # amoffat/sh with pytest capsys, configures sane defaults for testing,
    # bridges commands with configured environment.

    logging.getLogger('sh').setLevel(logging.INFO)

    # Monckey-patch commands defaults with sane values for testing.
    mod = sh._SelfWrapper__self_module
    mod.Command._call_args.update(dict(
        # Default to temboard scripts environment.
        env=ui_env,
        # Send stderr & stdout to pytest capsys.
        err=partial(stdio_writer_callback, sys.stderr),
        out=partial(stdio_writer_callback, sys.stdout),
        # Still capture output for assert.
        tee="out",
    ))

    # Don't truncate stderr on error.
    mod.ErrorReturnCode.__init__.__defaults__ = (False,)


def stdio_writer_callback(fo, data):
    # IO callback for amoffat/sh
    fo.write(data)
    return False  # should_quit


@pytest.fixture(scope='session')
def workdir(request):
    """
    Create a FHS-like tree in tests/workdir.
    """

    if 'CI' in os.environ:
        logger.info("Working in root filesystem.")
        root = Path('/')

        yield root
    else:
        path = Path(request.config.rootdir) / 'workdir'
        logger.info("Working in local work directory %s.", path)
        if path.exists():
            logger.info("Cleaning existing %s.", path)
            rmtree(path)

        path.mkdir()
        for name in 'etc', 'etc/pki', 'run', 'var', 'var/log':
            (path / name).mkdir()

        yield path

        logger.info("Cleaning %s.", path)
        rmtree(path)
