import logging

import pytest
from sh import SignalException


logger = logging.getLogger(__name__)


def test_running(browser, pg_sleep, registered_agent, ui_url):
    browser.get(ui_url)
    browser.select("a.instance-link").click()
    browser.select("div.sidebar a.activity").click()

    # Pause auto-refresh
    browser.select("td input[type=checkbox]").click()
    auto_refresh_resume = browser.select("span#autoRefreshResume")
    assert 'd-none' not in auto_refresh_resume.get_attribute('class')

    td = browser.select('td.query')

    assert 'pg_sleep' in td.text
    assert 'test-activity' in td.text


@pytest.fixture
def pg_sleep(psql):
    """Ensure a backend is running for 30s in monitored Postgres."""
    logger.info("Starting pg_sleep in background.")
    proc = psql(
        c="SELECT pg_sleep(30), 'test-activity';",
        _bg=True)
    assert proc.is_alive()

    yield proc

    logger.info("Stopping pg_sleep.")
    terminate(proc)


@pytest.fixture(scope='module')
def psql(postgres, sudo_pguser, agent_env):
    """Returns a psql command line to monitored Postgres."""
    return sudo_pguser.psql.bake(
        _env=dict(agent_env, PGAPPNAME='pytest-psql'),
        _bg_exc=False,
    )


def terminate(proc):
    if not proc.is_alive():
        return

    proc.terminate()

    try:
        proc.wait(timeout=5)
    except SignalException:
        pass

    return proc
