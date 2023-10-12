import csv
import logging
import os.path
import subprocess
import sys
from base64 import b64decode
from errno import ENOTEMPTY
from getpass import getuser
from pathlib import Path
from textwrap import dedent
from uuid import uuid4

import httpx
import pytest
from selenium.common import exceptions as selenium_exc
from selenium.webdriver import Remote
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import (
    Options as FirefoxOptions)
from selenium.webdriver.firefox.remote_connection import (
    FirefoxRemoteConnection)
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from sh import (
    ErrorReturnCode, TimeoutException,
    env as env_cmd, hostname,
    # Use bare sudo instead of contrib to ensure non interactive sudo.
    sudo,
)

from .utils import copy_files, retry_http, retry_slow, session_tag


logger = logging.getLogger(__name__)


class Browser:
    Keys = Keys

    # Helper for selenium API.
    def __init__(self, webdriver):
        self.webdriver = webdriver

    UNDEFINED = object()

    def __getattr__(self, name, default=UNDEFINED):
        value = getattr(self.webdriver, name, default)
        if value is self.UNDEFINED:
            raise AttributeError(name)
        return value

    def absent(self, selector, timeout=3):
        # Waits until an element vanish.
        return WebDriverWait(self.webdriver, timeout).until_not(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, selector)),
            f"Element {selector} is still present.",
        )

    def get_full_page_screenshot_as_png(self):
        return self.select("body").screenshot_as_png

    def hidden(self, selector, timeout=3, check='class'):
        return WebDriverWait(self.webdriver, timeout).until_not(
            expected_conditions.visibility_of_element_located(
                (By.CSS_SELECTOR, selector)
            )
        )

    def hover(self, selector):
        (
            ActionChains(self.webdriver)
            .move_to_element(self.select(selector))
            .perform()
        )

    def refresh_until(self, selector):
        for attempt in retry_slow(selenium_exc.NoSuchElementException):
            with attempt:
                try:
                    return self.select(selector)
                except selenium_exc.NoSuchElementException:
                    self.refresh()
                    raise

    def select(self, selector):
        return self.webdriver.find_element(by=By.CSS_SELECTOR, value=selector)

    def select_all(self, selector):
        return self.webdriver.find_elements(by=By.CSS_SELECTOR, value=selector)

    def list_download_filenames(self):
        self.webdriver.command_executor._commands["SET_CONTEXT"] = (
            "POST", "/session/$sessionId/moz/context")
        self.webdriver.execute("SET_CONTEXT", {"context": "chrome"})
        filenames = self.webdriver.execute_async_script(dedent("""\
        var { Downloads } = Components.utils.import('resource://gre/modules/Downloads.jsm', {});
        Downloads.getList(Downloads.ALL)
        .then(list => list.getAll())
        .then(entries => entries.filter(e => e.succeeded).map(e => e.target.path))
        .then(arguments[0]);
        """))  # noqa: E501
        self.webdriver.execute("SET_CONTEXT", {"context": "content"})
        return filenames

    def fetch_remote_file(self, path):
        self.webdriver.execute("SET_CONTEXT", {"context": "chrome"})
        logger.info("Downloading %s.", path)
        contents = self.webdriver.execute_async_script(dedent("""\
        var { OS } = Cu.import("resource://gre/modules/osfile.jsm", {});
        OS.File.read(arguments[0]).then(function(data) {
        var base64 = Cc["@mozilla.org/scriptablebase64encoder;1"].getService(Ci.nsIScriptableBase64Encoder);
        var stream = Cc['@mozilla.org/io/arraybuffer-input-stream;1'].createInstance(Ci.nsIArrayBufferInputStream);
        stream.setData(data.buffer, 0, data.length);
        return base64.encodeToString(stream, data.length);
        }).then(arguments[1]);
        """), path)  # noqa: E501
        self.webdriver.execute("SET_CONTEXT", {"context": "content"})
        binary_contents = b64decode(contents)

        # Save a local copy.
        localfile = self.downloads_dir / Path(path).name
        logger.info("Saving file %s.", localfile)
        localfile.write_bytes(binary_contents)
        return binary_contents


def text_to_be_present_in_element_attribute(locator, attribute_, text_):
    def _predicate(driver):
        try:
            element_text = driver.find_element(*locator).get_attribute(
                attribute_)
            return text_ in element_text
        except selenium_exc.StaleElementReferenceException:
            return False

    return _predicate


@pytest.fixture(scope='session')
def admin_session(browser_session, ui, ui_url):
    """Ensure temBoard UI is opened in browser and admin is logged in."""

    browser = browser_session
    browser.get(ui_url + '/login')
    browser.select("#inputUsername").send_keys("admin")
    browser.select("#inputPassword").send_keys("admin")
    browser.select("button[type=submit]").click()

    return browser


@pytest.fixture(scope='session')
def apikey(ui_auto_configure, ui_sudo):
    # Creates a session-wide temBoard API key
    out = ui_sudo.temboard.apikey.create()
    reader = csv.reader(out)
    headers = next(reader)
    assert 'Secret' == headers[1]
    _, secret, *_ = next(reader)
    return secret


@pytest.fixture(scope='module')
def browse_instance(browser_session, registered_agent, ui_url):
    """Open first instance in temBoard UI home."""
    browser = browser_session
    browser.get(ui_url)  # Goto home
    browser.select("a.instance-link").click()  # Click first instance


@pytest.fixture(scope='session')
def browser_session(request, ui, ui_url):
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
    options = FirefoxOptions()
    # Avoid download panel, which may occult view. We won't interract with it.
    # See Browser.list_download_filenames() and Browser.fetch_remote_file().
    options.set_preference("browser.download.alwaysOpenPanel", False)
    # Don't use default Downloads
    options.set_preference("browser.download.folderList", 2)
    downloaddir = f"/home/seluser/Downloads/{uuid4()}"
    options.set_preference("browser.download.dir", downloaddir)
    driver = Remote(command_executor=connection, options=options)
    driver.implicitly_wait(3)

    # Open UI and ensure login prompt is shown
    browser = Browser(driver)

    browser.screenshots_dir = Path('tests/screenshots')
    browser.screenshots_dir.mkdir(exist_ok=True)
    browser.downloads_dir = Path('tests/downloads')
    browser.downloads_dir.mkdir(exist_ok=True)

    browser.get(ui_url + '/')
    browser.select("#inputUsername")

    yield browser

    logger.info("Closing browser.")
    driver.quit()

    try:
        browser.screenshots_dir.rmdir()
    except OSError as e:
        if ENOTEMPTY != e.errno:
            raise


@pytest.fixture
def browser(browser_session, request):
    """Handle browser per single test."""
    yield browser_session

    if hasattr(request.node, 'rep_call') and request.node.rep_call.passed:
        return

    filename = f"{session_tag}_{request.node.nodeid}.png"
    path = browser_session.screenshots_dir / filename
    png = browser_session.get_full_page_screenshot_as_png()
    with path.open('wb') as fo:
        fo.write(png)
    logger.info("Browser screenshot saved at %s.", path)

    filename = f"{session_tag}_{request.node.nodeid}.html"
    path = browser_session.downloads_dir / filename
    with path.open('w', encoding='utf-8') as fo:
        fo.write(browser_session.page_source)
    logger.info("HTML document saved at %s.", path)


@pytest.fixture(scope='session')
def registered_agent(
        admin_session, agent, agent_conf, browser_session, pg_version):
    """
    Ensure the temBoard agent and UI are running, and temBoard agent is
    registered in UI.
    """

    browser = browser_session
    browser.select("a[href='/settings/instances']").click()

    browser.select("button#buttonNewInstance").click()

    browser.select("input#inputAgentAddress").send_keys("0.0.0.0")
    port = agent_conf.get('temboard', 'port')
    browser.select("input#inputAgentPort").send_keys(port)
    browser.select("#buttonDiscover").click()
    browser.select("div#divGroups button.multiselect").click()
    browser.select("input[value='default']").click()
    browser.select("textarea#inputComment").send_keys("Registered by tests.")

    browser.select("#buttonSubmit").click()
    td = browser.select("td.agent_hostport")
    assert f'0.0.0.0:{port}' in td.text

    # Ensure modal succeed and hides.
    browser.hidden("#modalNewInstance")

    # Wait for one agent edit button to come up.
    browser.select("table tbody tr td button.btn-outline-secondary")

    # We should restart UI here to triggers monitoring and statements
    # background tasks, saving one round of 60s of waiting.

    return browser


@pytest.fixture(scope='session')
def ui(ui_auto_configure, ui_env, ui_sudo, ui_url, workdir) -> httpx.Client:
    """
    Starts temBoard UI, wait for UI to answer and returns an httpx client
    backed to query temBoard UI.

    User browser fixture to access temBoard UI with selenium.
    """

    logger.info("Starting temBoard UI.")
    proc = ui_sudo.temboard(config=ui_env['TEMBOARD_CONFIGFILE'], _bg=True)

    client = httpx.Client(base_url=ui_url, verify=False)
    client.proc = proc

    try:
        logger.info("Waiting for UI to come up.")
        for attempt in retry_http():
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

    if 'CI' not in os.environ:
        return

    candidates = [
        workdir / 'var/log/temboard-auto-configure.log',
        workdir / 'var/log/temboard/serve.log',
        workdir / 'var/log/ui/auto-configure.log',
        workdir / 'var/log/ui/serve.log',
    ]
    copy_files(candidates, Path("tests/logs"))


@pytest.fixture(scope='session')
def ui_auto_configure(ui_sharedir, env, ui_env, ui_sysuser, workdir: Path):
    """
    Configure UI with auto_configure.sh in tests/workdir/.
    """

    dirname = 'temboard' if 'CI' in os.environ else 'ui'
    auto_configure = ui_sharedir / 'auto_configure.sh'

    env = dict(
        env,
        TEMBOARD_DATABASE=ui_env['PGDATABASE'],
        TEMBOARD_PASSWORD=ui_env['PGPASSWORD'],
        TEMBOARD_PORT=ui_env['TEMBOARD_PORT'],
    )
    if 'CI' in os.environ:
        logfile = workdir / 'var/log/temboard-auto-configure.log'
        logdir = logfile.parent / 'temboard'
    else:
        logfile = workdir / 'var/log/ui/auto-configure.log'
        logfile.parent.mkdir(exist_ok=True)
        logdir = logfile.parent
        env.update(dict(
            ETCDIR=str(workdir / 'etc/ui'),
            VARDIR=str(workdir / 'var/ui'),
            LOGDIR=str(logfile.parent),
            SYSUSER=ui_sysuser,
        ))
    env['LOGFILE'] = str(logfile)

    logger.info("Calling %s.", auto_configure)
    try:
        subprocess.run(
            [auto_configure], env=env,
        ).check_returncode()
    except Exception:
        sys.stderr.write(logfile.read_text())
        raise

    extra_etc = workdir / 'etc' / dirname / 'temboard.conf.d/tests-extra.conf'
    extra_etc.parent.mkdir()
    extra_etc.write_text(dedent(f"""\
    [auth]
    allowed_ip = 10.0.0.0/8,127.0.0.0/8,172.16.0.0/12,192.168.0.0/16

    [logging]
    method = file
    destination = {logdir}/serve.log
    level = DEBUG
    """))

    yield None

    logger.info("Purging UI installation.")
    purge = ui_sharedir / 'purge.sh'
    try:
        subprocess.run(
            [purge], env=env,
        ).check_returncode()
    except Exception:
        sys.stderr.write(logfile.read_text())
        raise


@pytest.fixture(scope='session')
def ui_env(env, workdir):
    """
    Configure environment for temBoard UI processes.
    """

    dirname = 'temboard' if 'CI' in os.environ else 'ui'
    return dict(
        env,
        PGUSER='temboard',
        PGPASSWORD='temboard',
        PGDATABASE='temboardtest',
        TEMBOARD_CONFIGFILE=str(workdir / 'etc' / dirname / 'temboard.conf'),
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
def ui_sudo(ui_env, ui_sysuser):
    """Returns amoffat/sh command to eventually sudo to UI Unix user."""
    if ui_sysuser == getuser():
        cmd = env_cmd
    else:
        cmd = sudo.bake(
            non_interactive=True, set_home=True, preserve_env=True,
            user=ui_sysuser,
            _in=None,
        )
        cmd = cmd.bake("env")

    return cmd.bake(f"PATH={os.environ['PATH']}", _env=ui_env)


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


@pytest.fixture
def query_agent(agent, ui_auto_configure, ui_env, ui_sudo):
    # Workaround a mis-behaviour with amoffat/sh on Python 3.10 where stdout is
    # empty.
    def client(path):
        url = f"{agent.base_url}{path}"
        proc = subprocess.Popen(
            [ui_sudo._path] + ui_sudo._partial_baked_args +
            ['temboard', 'query-agent', url],
            env=ui_env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        proc.stdin.close()
        proc.wait()
        # Copy to capsys
        for line in proc.stderr:
            sys.stderr.buffer.write(line)
        assert 0 == proc.returncode
        return proc.stdout.read()

    return client
