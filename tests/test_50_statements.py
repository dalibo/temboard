# Statements data are the slowest to come up. Thus this module us executed
# last.

import pytest

pytestmark = pytest.mark.slowstatements


def test_wait_for_data(browser, ensure_statements_data, ui_sudo):
    tds = browser.select_all(".main table tr td.database")
    databases = sorted([td.text for td in tds])
    assert "postgres" in databases


def test_picker(browser, browse_statements, ensure_statements_data):
    browser.select("#buttonPicker").click()


def test_refresh(browser, browse_statements, ensure_statements_data):
    browser.select("#buttonRefresh").click()
    browser.select("#buttonAutoRefresh").click()

    browser.select(".refresh-1m").click()
    assert "1m" == browser.select("#buttonAutoRefresh span").text

    browser.select("#buttonAutoRefresh").click()
    browser.select(".refresh-off").click()


def test_charts(browser, browse_statements, ensure_statements_data):
    # span ensure chart is drawn.
    browser.select("#legend-chart1 span")
    browser.select("#legend-chart2 span")
    browser.select("#legend-chart3 span")


def test_database(browser, browse_statements, ensure_statements_data):
    for a in browser.select_all(".main td.database a"):
        if "postgres" == a.text:
            a.click()
            break

    assert "postgres" == browser.select(".main .breadcrumb-item strong").text

    all_queries = browser.select_all(".main td.query pre.sql")
    assert 1 < len(all_queries)
    assert "SELECT" in "\n".join(q.text for q in all_queries)

    # Filter
    browser.select("#filterInput").send_keys("pg_sett")
    matched_queries = browser.select_all(".main td.query pre.sql")
    assert len(all_queries) >= len(matched_queries)
    for td in matched_queries:
        assert "pg_settings" in td.text

    # Reset filter
    browser.select("#buttonClearFilter").click()
    assert len(all_queries) <= len(browser.select_all(".main td.query"))

    # Go back to all databases
    browser.select(".main .breadcrumb-item a").click()
    browser.select(".main td.database")


def test_query(browser, browse_statements, ensure_statements_data):
    browser.select(".main td.database a").click()
    browser.select(".main td.query pre.sql").click()

    # Ensure full SQL query is detailed an highlighed.
    browser.select(".main tr.b-table-details pre.hljs")


@pytest.fixture
def browse_statements(browse_instance, browser):
    """Go to Statements tab of current instance."""
    browser.select("div.sidebar a.statements").click()


@pytest.fixture(scope="module")
def ensure_statements_data(agent_conf, browse_instance, browser_session, ui_sudo):
    """Waits for statements data to come up."""
    browser = browser_session
    browser.select("div.sidebar a.statements").click()
    browser.refresh_until(".main table tr td.database")
