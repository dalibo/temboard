import errno
import json
import logging
from queue import Queue
from time import sleep

import pytest
from sh import ErrorReturnCode, SignalException
from selenium.webdriver.common.by import By

from fixtures.utils import retry_fast


logger = logging.getLogger(__name__)


def test_running(browser, pg_sleep, registered_agent, ui_url):
    browser.get(ui_url)  # Goto home
    browser.select("a.instance-link").click()  # Click first instance
    browser.select("div.sidebar a.activity").click()  # Click Activity

    # Pause auto-refresh
    browser.hover(".main tr td.query")

    for tr in browser.select_all('.main tbody tr'):
        query = tr.find_element(By.CSS_SELECTOR, 'td.query pre')
        if 'test-activity' in query.text:
            tr.find_element(By.CSS_SELECTOR, 'input[type=checkbox]').click()
            break
    else:
        assert False, "pg_sleep not running"

    # Ensure auto_refresh button is shown
    auto_refresh_resume = browser.select("span#autoRefreshResume")
    assert 'd-none' not in auto_refresh_resume.get_attribute('class')

    browser.select("#killButton").click()  # Click read Terminate
    browser.select("#submitKill").click()  # Confirmation dialog

    # Ensure psql session is killed.
    with pytest.raises(ErrorReturnCode) as ei:
        pg_sleep.wait(timeout=1)

    assert 2 == ei.value.exit_code

    # Ensure processes vanished from view.
    sleep(.1)
    try:
        query = browser.absent("td.query").text
    except Exception:
        pass
    else:
        # If a query is running, ensure it's not pg_sleep.
        assert 'pg_sleep' not in query


def test_blocking_waiting(browser, pg_lock, registered_agent, ui_url):
    browser.get(ui_url)  # Goto home
    browser.select("a.instance-link").click()  # Click first instance
    browser.select("div.sidebar a.activity").click()  # Click Activity

    browser.select('td.query')  # Wait for queries to appears.

    for attempt in retry_fast():  # Wait for waiting count to come up
        with attempt:
            assert "1" == browser.select("#waiting-count").text

    browser.select(".nav-tabs a.waiting").click()  # Go to waiting tab

    # Pause auto-refresh
    browser.select("td input[type=checkbox]").click()
    # Ensure auto_refresh button is shown
    auto_refresh_resume = browser.select("span#autoRefreshResume")
    assert 'd-none' not in auto_refresh_resume.get_attribute('class')

    td = browser.select('td.query')
    assert 'UPDATE locked_table' in td.text

    assert "1" == browser.select("#blocking-count").text
    browser.select(".nav-tabs a.blocking").click()  # Go to blocking tab

    # Pause auto-refresh
    browser.select("td input[type=checkbox]").click()
    # Ensure auto_refresh button is shown
    auto_refresh_resume = browser.select("span#autoRefreshResume")
    assert 'd-none' not in auto_refresh_resume.get_attribute('class')

    td = browser.select('td.query')
    assert 'LOCK TABLE locked_table' in td.text


def test_locks(query_agent, pg_lock):
    out = query_agent('/activity/locks')
    data = json.loads(out)
    assert data['rows']

    waiting = False
    blocking = False
    for row in data['rows']:
        waiting = waiting or not row['granted']
        blocking = blocking or len(row['waiting_pids']) > 0

    assert waiting
    assert blocking


def test_sessions(query_agent, pg_lock):
    out = query_agent('/activity/sessions')
    data = json.loads(out)
    assert data['rows']

    waiting = False
    blocking = False
    for row in data['rows']:
        waiting = waiting or row['waiting']
        blocking = blocking or row['blocking']
        assert row['proc_state'] in ('R', 'S', 'D', None)

    assert waiting
    assert blocking


@pytest.fixture
def pg_lock(psql, agent_env):
    """Ensure one backend is waiting for another in monitored postgres."""
    EOF = None  # For amoffat/sh stdin Queue.

    locking = psql(_in=Queue(), _bg=True, _iter_noblock=True)
    locking.process.stdin.put("DROP TABLE IF EXISTS locked_table;\n")
    locking.process.stdin.put(
        "CREATE TABLE locked_table AS SELECT generate_series(1, 5);\n")

    table_created = False
    for attempt in retry_fast(OSError):
        with attempt:
            for _ in range(1000):
                line = next(locking)
                if line == errno.EWOULDBLOCK:
                    raise OSError()
                if line.startswith('SELECT 5'):
                    logger.info("locked_table created.")
                    table_created = True
                    break
    assert table_created, "Timeout creating table"

    locking.process.stdin.put("BEGIN;\n")
    locking.process.stdin.put("LOCK TABLE locked_table IN EXCLUSIVE MODE;\n")
    assert locking.is_alive()

    logger.info("Starting waiting process.")
    waiting = psql(_in=Queue(), _bg=True)
    waiting.process.stdin.put(
        "UPDATE locked_table SET generate_series = generate_series + 1;\n")
    assert waiting.is_alive()

    yield None

    waiting.process.stdin.put(EOF)
    locking.process.stdin.put(EOF)
    terminate(locking)
    terminate(waiting)


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


def terminate(proc):
    if not proc.is_alive():
        return

    proc.terminate()

    try:
        proc.wait(timeout=5)
    except SignalException:
        pass

    return proc
