# Testing monitoring after other plugins so that Agent and UI have the time to
# collect some data while other tests are running.

import logging

import pytest
from selenium.common.exceptions import TimeoutException

from fixtures.utils import retry_slow


logger = logging.getLogger(__name__)


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


@pytest.fixture
def browse_monitoring(browse_instance, browser):
    """Go to Monitoring tab of current instance."""
    browser.select("div.sidebar a.monitoring").click()

    # Zoom charts for screenshots.
    browser.select("#buttonPicker").click()
    browser.select("a[data-from=now-15m]").click()


@pytest.fixture(scope='module')
def ensure_monitoring_data(
        agent_conf, agent, browse_instance, browser_session, registered_agent,
        ui_sudo):
    """Ensure agent process has two minutes running."""
    browser = browser_session
    browser.select("div.sidebar a.monitoring").click()
    ui_sudo.temboard.schedule(
        "collector", "0.0.0.0", str(agent_conf['temboard']['port']),
    )

    browser.refresh_until("#nodataCPU")

    for attempt in retry_slow(TimeoutException):
        with attempt:
            browser.refresh()
            browser.hidden("#nodataCPU")
