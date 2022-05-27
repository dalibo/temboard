# Testing monitoring after other plugins so that Agent and UI have the time to
# collect some data while other tests are running.
#
# fixture/agent.py schedule probing each 5s. fixture/ui.py schedule collect
# each 5s.
#
import logging

import pytest
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from tenacity import (
    Retrying, retry_if_exception_type, stop_after_delay,
    wait_chain, wait_fixed,
)


logger = logging.getLogger(__name__)


def test_quick_alerting(browser, browse_alerting):
    # Quick pentest of status page.
    browser.select("#checks-container")


def test_quick_monitoring(browser, browse_monitoring):
    # Quick pentest of the monitoring page
    browser.select("a[aria-controls=metrics]").click()
    browser.select("#buttonPicker").click()


@pytest.mark.slowmonitoring
def test_wait_for_data(browser, browse_monitoring, ensure_monitoring_data):
    # Dumb test to show an explicit "wait_for_data" in pytest output.
    browser.select("#chartLoadavg")


@pytest.mark.slowmonitoring
def test_show_hide_chart(browser, browse_monitoring, ensure_monitoring_data):
    browser.select("a[aria-controls=metrics]").click()

    browser.absent("#chartCtxForks")  # No chart.
    browser.select("#checkboxCtxForks").click()  # Enable chart
    browser.select("#chartCtxForks")  # Ensure chart is shown
    browser.select("#checkboxCtxForks").click()  # Disable chart
    browser.absent("#chartCtxForks")  # Chart's vanished


@pytest.mark.slowmonitoring
def test_alerts(browser, browse_alerting, ensure_monitoring_data):
    checks = [
        'btree_bloat',
        'cpu_core',
        'heap_bloat',
        'hitreadratio_db',
        'load1',
        'memory_usage',
        'rollback_db',
        'sessions_usage',
        'temp_files_size_delta',
        'waiting_sessions_db',
        'wal_files_archive',
        'wal_files_total',
    ]

    wanted = {'badge-ok', 'badge-warning', 'badge-critical'}

    for check in checks:
        # Wait and refresh for probes to come up.
        for attempt in retry_one_minute(NoSuchElementException):
            with attempt:
                try:
                    el = browser.select(f"#status-{check} .badge")
                except Exception:
                    browser.refresh()
                    raise

        classes = set(el.get_attribute('class').split())
        assert wanted & classes


def retry_one_minute(exc_type=NoSuchElementException):
    return Retrying(
        retry=retry_if_exception_type(exc_type),
        stop=stop_after_delay(70),
        wait=wait_chain(
            *[wait_fixed(10)] * 2,
            wait_fixed(2),
        ),
    )


@pytest.fixture
def browse_alerting(agent_login, browse_instance, browser):
    """Go to Monitoring tab of current instance."""
    browser.select("div.sidebar a.alerting").click()


@pytest.fixture
def browse_monitoring(agent_login, browse_instance, browser):
    """Go to Monitoring tab of current instance."""
    browser.select("div.sidebar a.monitoring").click()

    # Zoom charts for screenshots.
    browser.select("#buttonPicker").click()
    browser.select("a[data-from=now-15m]").click()


@pytest.fixture(scope='module')
def ensure_monitoring_data(
        agent, browse_instance, browser_session, registered_agent):
    """Ensure agent process has two minutes running."""
    browser = browser_session
    browser.select("div.sidebar a.monitoring").click()

    for attempt in retry_one_minute(TimeoutException):
        with attempt:
            browser.refresh()
            browser.select("#nodataCPU")

    for attempt in retry_one_minute(TimeoutException):
        with attempt:
            browser.refresh()
            browser.hidden("#nodataCPU")
