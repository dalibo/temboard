import logging

from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)


def test_explain(browser, registered_agent, ui_url):
    browser.get(ui_url)  # Goto home
    browser.select("a.instance-link").click()  # Click first instance
    browser.select("div.sidebar a.explain").click()  # Click Explain

    browser.webdriver.find_element(By.XPATH, "//button[contains(., 'VERBOSE')]").click()

    browser.webdriver.find_element(By.ID, "query").send_keys("""
        SELECT * from pg_class;
    """)
    browser.webdriver.find_element(
        By.XPATH, "//button[@type='submit' and contains(., 'Explain')]"
    ).click()

    # Check that there's a valid element for PEV2 plan container with a node
    browser.select(".plan-container")
    browser.webdriver.find_element(
        By.XPATH,
        ".//div[contains(@class, 'plan-node') and contains(., 'pg_catalog.pg_class')]",
    )

    browser.webdriver.find_element(
        By.XPATH, "//button[contains(., 'Explain other query')]"
    ).click()


def test_explain_from_activity(browser, registered_agent, ui_url):
    browser.get(ui_url)  # Goto home
    browser.select("a.instance-link").click()  # Click first instance
    browser.select("div.sidebar a.activity").click()  # Click Activity

    # Pause auto-refresh
    browser.hover(".main tr td.query")
    browser.select(".main tr:nth-child(1) td.query span[data-testid=explain]").click()

    query = browser.webdriver.find_element(By.ID, "query").get_attribute("value")
    assert any(x in query for x in ["SELECT", "pg_size_pretty"])
