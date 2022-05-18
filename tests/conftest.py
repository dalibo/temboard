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
import subprocess
import sys
from configparser import ConfigParser
from contextlib import contextmanager
from functools import partial
from getpass import getuser
from glob import iglob
from pathlib import Path
from textwrap import dedent

import httpx
import pytest
import sh
from selenium.webdriver import Remote
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import (
    Options as FirefoxOptions)
from selenium.webdriver.firefox.remote_connection import (
    FirefoxRemoteConnection)
from sh import (
    ErrorReturnCode, TimeoutException,
    chown, env as env_cmd, hostname, locale, temboard, temboard_agent,
    # Use bare sudo instead of contrib to ensure non interactive sudo.
    sudo,
)
from tenacity import (
    Retrying, retry_if_exception_type, wait_fixed, stop_after_delay,
)


logger = logging.getLogger(__name__)


class Browser:
    # Helper for selenium API.
    def __init__(self, webdriver):
        self.webdriver = webdriver

    def select(self, selector):
        return self.webdriver.find_element(by=By.CSS_SELECTOR, value=selector)

    def __getattr__(self, name, default=None):
        return getattr(self.webdriver, name, default)


class PostgreSQLVersions(dict):
    # A mapping from major version -> bindir.

    # List of agent supported PostgreSQL versions.
    SUPPORTED_VERSIONS = [
        '14',
        '13',
        '12',
        '11',
        '10',
        '9.6',
        '9.5',
        '9.4',
    ]

    def search_installed_versions(self):
        patterns = [
            '/usr/lib/postgresql/*/bin/initdb',
            '/usr/pgsql-*/bin/initdb',
            '/usr/local/bin/initdb',
            '/usr/bin/initdb',
        ]
        for pattern in patterns:
            for initdb in iglob(pattern):
                res = subprocess.run(
                    [initdb, "--version"], stdout=subprocess.PIPE)
                res.check_returncode()
                out = res.stdout.decode('utf-8').split()
                assert 'initdb' == out[0]
                assert '(PostgreSQL)' == out[1]
                version = out[2]
                if not version.startswith('9.'):
                    version, _ = version.split('.')
                else:
                    version = version[:3]

                bindir = str(Path(initdb).parent)
                if version in self:
                    logger.info(
                        "Found duplicate installation for %s at %s.",
                        version, bindir,
                    )
                elif version in self.SUPPORTED_VERSIONS:
                    logger.info(
                        "Found supported version %s at %s.",
                        version, bindir,
                    )
                    self[version] = bindir
                else:
                    logger.info(
                        "Found unsupported version %s at %s.",
                        version, bindir)

    @property
    def most_recent_version(self):
        sorted_version = sorted(
            self.keys(),
            key=float,
            reverse=True,
        )
        return sorted_version[0]


POSTGRESQL_AVAILABLE_VERSIONS = PostgreSQLVersions()


@pytest.fixture(scope='session', autouse=True)
def activate_virtualenv():
    """Automatically activate temBoard UI virtualenv on debian."""

    bindir = Path('/usr/lib/temboard/bin/')
    if bindir.exists():
        logger.debug("Activating %s virtualenv.", bindir.parent)
        os.environ['PATH'] = f"{bindir}:{os.environ['PATH']}"


@pytest.fixture(scope='session')
def admin_session(browser, ui, ui_url):
    """Ensure temBoard UI is opened in browser and admin is logged in."""

    browser.get(ui_url + '/login')
    browser.select("#inputUsername").send_keys("admin")
    browser.select("#inputPassword").send_keys("admin")
    browser.select("button[type=submit]").click()

    return browser


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


@pytest.fixture(scope='session')
def agent(agent_auto_configure, agent_env, pguser, sudo_pguser, workdir):
    """
    Run configured temBoard agent.

    The agent is a subprocess of pytest.
    """

    proc = sudo_pguser("temboard-agent", _bg=True, _env=agent_env)
    assert proc.is_alive()

    client = httpx.Client(
        base_url=f"https://localhost:{agent_env['TEMBOARD_PORT']}",
        verify=False,
    )
    for attempt in httpx_retry():
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
def browser(request, ui, ui_url):
    """
    Open session dedicated Firefox with temBoard UI opened.
    """

    logging.getLogger('selenium').setLevel(logging.ERROR)

    connection = FirefoxRemoteConnection(
        request.config.getoption("--selenium"),
    )
    connection.set_timeout(30)
    # Hack to apply timeout to urllib connection pool too.
    connection._conn.connection_pool_kw['timeout'] = 30
    logger.info("Opening browser.")
    # FirefoxOptions() changes default acceptInsecureCerts to True.
    driver = Remote(command_executor=connection, options=FirefoxOptions())
    driver.implicitly_wait(3)

    # Open UI and ensure login prompt is shown
    driver.get(ui_url + '/')
    browser = Browser(driver)
    browser.select("#inputUsername")

    try:
        yield browser
    finally:
        logger.info("Closing browser.")
        driver.quit()


@pytest.fixture(scope='session', autouse=True)
def env():
    """
    Configure environment with superuser privileges.

    This is the environment for auto_configure.sh scripts, etc.
    """

    # Configure libpq with superuser from docker-compose.yml
    os.environ.setdefault('PGUSER', 'postgres')
    os.environ.setdefault('PGPASSWORD', 'postgres')

    return os.environ


def find_locale():
    out = locale(a=True)
    for candidate in ('en_US', 'fr_FR'):
        candidate = candidate + '.utf8'
        if candidate in out:
            return candidate
    else:
        raise Exception("Missing en_US.utf8 locale.")


@pytest.fixture(scope='session')
def fqdn():
    """
    Determine host FQDN.
    """
    fqdn = str(hostname('--fqdn'))
    return fqdn if '.' in fqdn else 'localhost.localdomain'


def httpx_retry():
    return Retrying(
        retry=retry_if_exception_type((httpx.NetworkError, OSError)),
        stop=stop_after_delay(10),
        wait=wait_fixed(.1),
    )


@pytest.fixture(scope='session', autouse=True)
def log_tweaks():
    """
    Send logs to capsys instead of caplog.
    """

    formatter = logging.Formatter(
        fmt="[%(module)-16.16s] %(levelname)1.1s: %(message)s"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


@contextmanager
def nullcontext():
    yield None


@pytest.fixture(scope='session')
def postgres(agent_env, pguser, sudo_pguser, workdir):
    """
    Initialize a PostgreSQL instance for monitoring by a temBoard agent.

    pgdata is in tests/workdir/var/pgdata. Executes postgres as a subprocess
    of pytest. See pguser fixture for the process and files owner policy.

    Returns pgdata directory object.
    """

    # workdir fixture warranties an empty directory.
    pgdata = workdir / 'var/pgdata'
    logger.info("Creating %s.", pgdata)
    pgdata.mkdir()
    logdir = workdir / 'var/log/postgresql'
    logdir.mkdir()
    socketdir = Path(agent_env['PGHOST'])
    socketdir.mkdir()
    chown("--recursive", pguser, pgdata, logdir, socketdir)

    locale_ = find_locale()

    logger.info("Initializing database at %s.", pgdata)
    pwfile = workdir / 'pwfile'
    pwfile.write_text(agent_env['PGPASSWORD'])
    sudo_pguser.initdb(
            locale=locale_,
            username=agent_env['PGUSER'],
            auth_local="md5",
            pwfile=str(pwfile),
            pgdata=str(pgdata),
        )
    pwfile.unlink()

    auto = pgdata / 'postgresql.auto.conf'
    logger.info("Writing %s.", auto)
    config = auto.read_text()
    auto.write_text(dedent(f"""\
    {config}
    include_dir = 'conf.d'
    """))

    conffile = pgdata / 'conf.d' / 'temboard-tests.conf'
    conffile.parent.mkdir()
    logger.info("Writing %s.", conffile)
    pidfile = workdir / 'run/postgres.pid'
    conffile.write_text(dedent(f"""\
    cluster_name = 'temboard-tests'
    external_pid_file = '{pidfile}'
    log_directory = '{logdir}'
    log_line_prefix = '%t [%p]: user=%u,db=%d,app=%a,client=%h '
    logging_collector = on
    port = {agent_env['PGPORT']}
    unix_socket_directories = '{socketdir}'
    """))

    logger.info("Starting instance at %s.", pgdata)
    sudo_pguser.pg_ctl(f"--pgdata={pgdata}", "start")
    sudo_pguser.psql(c='SELECT version();', _env=agent_env)  # pentest

    yield pgdata

    logger.info("Stopping instance at %s.", pgdata)
    sudo_pguser.pg_ctl(f"--pgdata={pgdata}", "--mode=immediate", "stop")
    rmtree(pgdata)


@pytest.fixture(scope='session', autouse=True)
def pgbin(pg_version):
    """
    Inject in PATH PostgreSQL bin directory for chosen version.
    """

    bindir = POSTGRESQL_AVAILABLE_VERSIONS[pg_version]
    logger.info("Using %s.", bindir)
    os.environ['PATH'] = f"{bindir}:{os.environ['PATH']}"
    return bindir


@pytest.fixture(scope='session')
def pguser():
    """
    Determine UNIX user for executing Postgres and agent.
    """
    me = getuser()
    user = 'postgres' if 'root' == me else me
    logger.info("Using UNIX user %s for Postgres and agent.", user)
    return user


@pytest.fixture(scope='session')
def pg_version(request):
    """ Reads chosen PostgreSQL major version. """
    return request.config.getoption("--pg-version")


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


@pytest.fixture(scope='session')
def registered_agent(admin_session, agent, agent_conf, browser, pg_version):
    """
    Ensure the temBoard agent and UI are running, and temBoard agent is
    registered in UI.
    """

    browser.select("a[href='/settings/instances']").click()

    browser.select("button#buttonLoadAddInstanceForm").click()

    browser.select("input#inputNewAgentAddress").send_keys("0.0.0.0")
    port = agent_conf.get('temboard', 'port')
    browser.select("input#inputNewAgentPort").send_keys(port)
    key = agent_conf.get('temboard', 'key')
    browser.select("input#inputAgentKey").send_keys(key)
    browser.select("div#divSelectGroups button").click()
    browser.select("label[title='default']").click()
    browser.select("textarea#inputComment").send_keys("Registered by tests.")

    browser.select("button#submitFormAddInstance").click()

    return browser


def rmtree(root: Path):
    # Thanks to Jacques Gaudin, from
    # https://stackoverflow.com/questions/54697350/how-do-i-delete-a-directory-tree-with-pathlib.

    for path in root.iterdir():
        if path.is_dir():
            rmtree(path)
        else:
            path.unlink()

    root.rmdir()


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


@pytest.fixture(scope='session')
def ui(ui_auto_configure, ui_env, ui_sudo, ui_url) -> httpx.Client:
    """
    Starts temBoard UI, wait for UI to answer and returns an httpx client
    backed to query temBoard UI.

    User browser fixture to access temBoard UI with selenium.
    """

    logger.info("Starting temBoard UI.")
    proc = ui_sudo.temboard(config=ui_env['TEMBOARD_CONFIGFILE'], _bg=True)

    client = httpx.Client(base_url=ui_url, verify=False)

    try:
        for attempt in httpx_retry():
            with attempt:
                client.get('/')
        yield client
    finally:
        logger.info("Stopping temBoard UI.")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except TimeoutException:
            logger.info("Killing temBoard UI.")
            proc.kill()
            proc.wait(timeout=5)
        except ErrorReturnCode as e:
            logger.info("temBoard UI exited with code %s.", e.exit_code)


@pytest.fixture(scope='session')
def ui_auto_configure(ui_sharedir, env, ui_env, ui_sysuser, workdir):
    """
    Configure UI with auto_configure.sh in tests/workdir/.
    """

    from sh import dropdb

    auto_configure = ui_sharedir / 'auto_configure.sh'
    logger.info("Calling %s.", auto_configure)
    logfile = workdir / 'var/log/temboard/ui-auto-configure.log'
    logfile.parent.mkdir()
    try:
        subprocess.run([auto_configure], env=dict(
            env,
            ETCDIR=str(workdir / 'etc/temboard'),
            VARDIR=str(workdir / 'var/temboard'),
            LOGDIR=str(logfile.parent),
            LOGFILE=str(logfile),
            SYSUSER=ui_sysuser,
            TEMBOARD_DATABASE=ui_env['PGDATABASE'],
            TEMBOARD_PASSWORD=ui_env['PGPASSWORD'],
            TEMBOARD_PORT=ui_env['TEMBOARD_PORT'],
        )).check_returncode()
    except Exception:
        sys.stderr.write(logfile.read_text())
        raise

    yield None

    logger.info("Dropping database temboardtest.")
    dropdb('temboardtest')


@pytest.fixture(scope='session')
def ui_env(env, workdir):
    """
    Configure environment for temBoard UI processes.
    """

    return dict(
        env,
        PGUSER='temboard',
        PGPASSWORD='temboard',
        PGDATABASE='temboardtest',
        TEMBOARD_CONFIGFILE=str(workdir / 'etc/temboard/temboard.conf'),
        TEMBOARD_LOGGING_LEVEL='DEBUG',
        TEMBOARD_PORT='18888',
    )


@pytest.fixture(scope='session')
def ui_sharedir():
    """
    Search for UI share/ directory.
    """

    candidates = [
        # rpm/deb
        '/usr/share/temboard',
        # pip install
        '/usr/local/share/temboard',
        # development
        'ui/share/',
    ]

    for candidate in candidates:
        if os.path.isdir(candidate):
            logger.info("Using %s.", candidate)
            return Path(candidate)


@pytest.fixture(scope='session')
def ui_sudo(ui_sysuser):
    """Returns amoffat/sh command to eventually sudo to UI Unix user."""
    if ui_sysuser == getuser():
        return env_cmd
    else:
        return sudo.bake(
            non_interactive=True, set_home=True, preserve_env=True,
            user=ui_sysuser,
            _in=None,
        )


@pytest.fixture(scope='session')
def ui_sysuser():
    """
    Determine UNIX user to execute UI.
    """
    # If running as root (container mode), use temboard as created by packages
    # and auto_configure.sh. Else, use running user (development mode).
    me = getuser()
    user = 'temboard' if me == 'root' else me
    logger.info("Using UNIX user %s for UI.", user)
    return user


@pytest.fixture(scope='session')
def ui_url(ui_env):
    """
    Compute a routable base URL for temBoard UI.
    """
    out = hostname("--all-ip-addresses")
    ip, *_ = str(out).split()
    yield f"https://{ip}:{ui_env['TEMBOARD_PORT']}"


@pytest.fixture(scope='session')
def workdir(request):
    """
    Create a FHS-like tree in tests/workdir.
    """

    path = Path(request.config.rootdir) / 'workdir'
    if path.exists():
        logger.info("Cleaning existing %s.", path)
        rmtree(path)

    logger.info("Creating %s.", path)
    path.mkdir()
    for name in 'etc', 'etc/pki', 'run', 'var', 'var/log':
        (path / name).mkdir()

    yield path

    logger.info("Cleaning %s.", path)
    rmtree(path)
