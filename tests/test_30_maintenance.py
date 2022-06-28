from contextlib import suppress

import pytest
from tenacity import (
    Retrying, retry_unless_exception_type, stop_after_delay, wait_fixed,
)
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotInteractableException


def test_all_databases(browser, browse_maintenance):
    ol = browser.select("ol.breadcrumb")
    # Ensure there is a single li
    li, = ol.find_elements(By.TAG_NAME, 'li')
    assert 'All Databases' == li.text

    browser.select("td.database")
    browser.select("td.temboard-tables span.badge")
    browser.select("td.temboard-tables .table-bloat")
    browser.select("td.indexes span.badge")
    browser.select("td.indexes .index-bloat")
    browser.select("td.toast")


def test_database(browser, browse_maintenance):
    browser.select("td.database a").click()

    ol = browser.select("ol.breadcrumb")
    li0, li1 = ol.find_elements(By.TAG_NAME, 'li')
    assert 'All Databases' == li0.text
    assert 'postgres' in li1.text

    browser.select("#buttonAnalyze")
    browser.select("#buttonVacuum")
    browser.select("#buttonReindex")

    browser.select("td.schema")
    browser.select("td.temboard-tables span.badge")
    browser.select("td.temboard-tables .table-bloat")
    browser.select("td.indexes span.badge")
    browser.select("td.indexes .index-bloat")


def test_database_analyze_now(browser, browse_maintenance):
    browser.select("td.database a").click()

    browser.select("#buttonAnalyze").click()

    # In modal
    browser.select("#analyzeNow").click()
    browser.select("#analyzeScheduled")
    # Hack some weird case where button.click() is not effective. Need more
    # investigation.
    for attempt in retry_until_hidden():
        with attempt:
            browser.select("#buttonAnalyzeApply").click()

    browser.hidden("#analyzeModal")
    browser.absent(".modal-backdrop")


def test_database_vacuum_now(browser, browse_maintenance):
    browser.select("td.database a").click()

    browser.select("#buttonVacuum").click()

    # In modal
    browser.select("#vacuumModeAnalyze").click()
    browser.select("#vacuumModeFull")
    browser.select("#vacuumModeFreeze")
    browser.select("#vacuumNow").click()
    for attempt in retry_until_hidden():
        with suppress(ElementNotInteractableException), attempt:
            browser.select("#buttonVacuumApply").click()

    browser.hidden("#vacuumModal")
    browser.absent(".modal-backdrop")


def test_database_reindex_now(browser, browse_maintenance):
    browser.select("td.database a").click()

    browser.select("#buttonReindex").click()

    # In modal
    browser.select("#reindexNow").click()
    browser.select("#reindexScheduled")
    for attempt in retry_until_hidden():
        with suppress(ElementNotInteractableException), attempt:
            browser.select("#buttonReindexApply").click()

    browser.hidden("#reindexModal")
    browser.absent(".modal-backdrop")


def test_schema(browser, browse_maintenance):
    browser.select("td.database a").click()
    browser.select("td.schema a").click()

    ol = browser.select("ol.breadcrumb")
    li0, li1, li2 = ol.find_elements(By.TAG_NAME, 'li')
    assert 'All Databases' == li0.text
    assert 'postgres' in li1.text
    assert 'pg_catalog' in li2.text

    browser.select("td.temboard-table")
    browser.select("td.temboard-table-total-size")
    browser.select("td.heap")
    browser.select("td.indexes span.badge")
    browser.select("td.indexes .index-bloat")
    browser.select("td.toast")


def test_schema_reindex_now(browser, browse_maintenance):
    browser.select("td.database a").click()
    browser.select("td.schema a").click()

    browser.select("td.reindex .buttonReindex").click()

    browser.select("#reindexNow").click()
    for attempt in retry_until_hidden():
        with suppress(ElementNotInteractableException), attempt:
            browser.select("#buttonReindexApply").click()

    browser.hidden("#reindexModal")
    browser.absent(".modal-backdrop")


def test_table(browser, browse_table):
    browser.select("#buttonAnalyze")
    browser.select("#buttonVacuum")
    browser.select("#buttonReindex")

    browser.select("td.index-name")
    browser.select("td.index-size")
    browser.select("td.index-scans span.badge")
    browser.select("td.query")
    browser.select("td.reindex")


def test_table_analyze_now(browser, browse_table):
    browser.select("#buttonAnalyze").click()

    # In modal
    browser.select("#analyzeNow").click()
    browser.select("#analyzeScheduled")
    for attempt in retry_until_hidden():
        with suppress(ElementNotInteractableException), attempt:
            browser.select("#buttonAnalyzeApply").click()

    browser.hidden("#analyzeModal")
    browser.absent(".modal-backdrop")


def test_table_vacuum_now(browser, browse_table):
    browser.select("#buttonVacuum").click()

    # In modal
    browser.select("#vacuumModeAnalyze").click()
    browser.select("#vacuumModeFull")
    browser.select("#vacuumModeFreeze")
    browser.select("#vacuumNow").click()
    for attempt in retry_until_hidden():
        with suppress(ElementNotInteractableException), attempt:
            browser.select("#buttonVacuumApply").click()

    browser.hidden("#vacuumModal")
    browser.absent(".modal-backdrop")


def test_table_reindex_now(browser, browse_table):
    browser.select("#buttonReindex").click()

    # In modal
    browser.select("#reindexNow").click()
    browser.select("#reindexScheduled")
    for attempt in retry_until_hidden():
        with suppress(ElementNotInteractableException), attempt:
            browser.select("#buttonReindexApply").click()

    browser.hidden("#reindexModal")
    browser.absent(".modal-backdrop")


@pytest.fixture
def browse_maintenance(browse_instance, browser):
    """Go to Maintenance tab of current instance."""
    browser.select("div.sidebar a.maintenance").click()


@pytest.fixture
def browse_table(browse_maintenance, browser):
    browser.select("td.database a").click()
    browser.select("td.schema a").click()
    browser.select("td.temboard-table a").click()


def retry_until_hidden():
    with suppress(ElementNotInteractableException):
        yield from Retrying(
            retry=retry_unless_exception_type(ElementNotInteractableException),
            stop=stop_after_delay(10),
            wait=wait_fixed(.1),
        )
