import logging
import os.path
import subprocess
import sys
from datetime import datetime
from errno import ENOTEMPTY
from getpass import getuser
from pathlib import Path
from textwrap import dedent

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

from fixtures.utils import retry_http, retry_slow


logger = logging.getLogger(__name__)


class Browser:
    Keys = Keys

    # Helper for selenium API.
    def __init__(self, webdriver):
        self.webdriver = webdriver
        self.screenshot_tag = datetime.now().strftime('%H%M%S')

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

    def hidden(self, selector, timeout=3):
        waiter = WebDriverWait(self.webdriver, timeout)
        element = self.select(selector)
        if 'dialog' == element.get_attribute('role'):
            callable_ = waiter.until_not
            attribute, value = 'class', 'show'
            message = f"Element {selector} {attribute} still has {value}.",
        else:
            callable_ = waiter.until
            attribute, value = 'class', 'd-none'
            message = f"Element {selector} {attribute} does not have {value}.",

        # Waits until an element has d-none.
        return callable_(
            text_to_be_present_in_element_attribute(
                (By.CSS_SELECTOR, selector),
                attribute, value,
            ),
            message,
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
def agent_login(alice, browser_session, registered_agent, ui_url):
    """Login with Alice to agent thru UI."""
    browser = browser_session

    browser.get(ui_url)  # Goto home
    browser.select("a.instance-link").click()  # Click first instance

    dashboard_url = browser.current_url
    assert dashboard_url.endswith('/dashboard')
    login_url = dashboard_url.replace('/dashboard', '/login')

    browser.get(login_url)
    browser.select("#inputUsername").send_keys("alice")
    browser.select("#inputPassword").send_keys("S3cret_alice")
    browser.select("form[action=login] button[type=submit]").click()
    browser.select("a.instance-link")  # Wait for home to load.

    browser.get(dashboard_url)  # Go back to dashboard.


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
    driver = Remote(command_executor=connection, options=FirefoxOptions())
    driver.implicitly_wait(3)

    # Open UI and ensure login prompt is shown
    browser = Browser(driver)

    browser.screenshots_dir = Path('tests/screenshots')
    browser.screenshots_dir.mkdir(exist_ok=True)

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

    if request.node.rep_call.passed:
        return

    filename = f"{browser_session.screenshot_tag}_{request.node.nodeid}.png"
    path = browser_session.screenshots_dir / filename
    png = browser_session.get_full_page_screenshot_as_png()
    with path.open('wb') as fo:
        fo.write(png)
    logger.info("Browser screenshot saved at %s.", path)


@pytest.fixture(scope='session')
def registered_agent(
        admin_session, agent, agent_conf, browser_session, pg_version):
    """
    Ensure the temBoard agent and UI are running, and temBoard agent is
    registered in UI.
    """

    browser = browser_session
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
    td = browser.select("td.agent_hostport")
    assert f'0.0.0.0:{port}' in td.text

    # Ensure modal succeed and hides.
    browser.hidden("#InstanceModal")

    # We should restart UI here to triggers monitoring and statements
    # background tasks, saving one round of 60s of waiting.

    return browser


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

    extra_etc = workdir / 'etc/temboard/temboard.conf.d/tests-extra.conf'
    extra_etc.parent.mkdir()
    extra_etc.write_text(dedent(f"""\
    [logging]
    method = file
    destination = {logfile.parent}/temboard.log
    level = DEBUG
    """))

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
