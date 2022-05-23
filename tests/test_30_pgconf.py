import pytest
from selenium.webdriver.support.select import Select


@pytest.fixture
def browse_pgconf(agent_login, browse_instance, browser):
    """Go to Configuration tab of current instance."""
    browser.select("div.sidebar a.pgconf").click()


def test_category_selector(browse_pgconf, browser):
    # Ensure some categories are listed
    browser.select("#selectConfCat option:nth-child(10)")

    selected_category = browser.select("#selectConfCat option[selected]").text
    current_category = browser.select(".card-header").text
    assert selected_category == current_category

    category_selector = Select(browser.select("#selectConfCat"))
    category_selector.select_by_visible_text('Error Handling')
    current_category = browser.select(".card-header").text
    assert 'Error Handling' == current_category
