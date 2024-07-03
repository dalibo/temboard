import pytest


def test_quick_alerting(browser, browse_alerting):
    # Quick smoketest of status page.
    browser.select("#checks-container")


@pytest.mark.slowmonitoring
def test_alerts(browser, browse_alerting):
    checks = [
        "btree_bloat",
        "cpu_core",
        "heap_bloat",
        "hitreadratio_db",
        "load1",
        "memory_usage",
        "rollback_db",
        "sessions_usage",
        "temp_files_size_delta",
        "waiting_sessions_db",
        "wal_files_archive",
        "wal_files_total",
    ]

    wanted = {"text-bg-ok", "text-bg-warning", "text-bg-critical"}

    for check in checks:
        el = browser.refresh_until(f"#status-{check} .badge")
        classes = set(el.get_attribute("class").split())
        assert wanted & classes


@pytest.fixture
def browse_alerting(browse_instance, browser):
    """Go to Monitoring tab of current instance."""
    browser.select("div.sidebar a.alerting").click()
