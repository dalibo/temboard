import pytest
from fixtures.utils import MultiSelect
from selenium.webdriver.common.by import By


@pytest.fixture(scope="module")
def browse_settings_instance_groups(browser_session, ui_url, admin_session):
    browser_session.get(ui_url + "/settings/groups/instance")


@pytest.fixture(scope="module")
def instance_group_prod(browse_settings_instance_groups, browser_session):
    browser_session.select("#buttonLoadAddGroupForm").click()
    browser_session.select("#inputNewGroupname").send_keys("prod")
    browser_session.select("#inputDescription").send_keys("Production")
    multiselect = MultiSelect(browser_session, "userGroups")
    multiselect.toggle().select("default")
    browser_session.select("button[type=submit]").click()


def test_create_instance_group(instance_group_prod, browser):
    assert any(
        "Production" in group.text
        for group in browser.select_all("#tableGroups tbody tr")
    )


def test_update_instance_group(instance_group_prod, browser):
    tr = [
        tr for tr in browser.select_all("#tableGroups tbody tr") if "prod" in tr.text
    ][0]

    tr.find_element(by=By.CSS_SELECTOR, value="[data-action=edit]").click()
    assert browser.select("#inputNewGroupname").get_attribute("value") == "prod"
    description_input = browser.select("#inputDescription")
    assert description_input.get_attribute("value") == "Production"

    description_input.send_keys(" and staging")
    browser.select("button[type=submit]").click()
    assert any(
        "Production and staging" in group.text
        for group in browser.select_all("#tableGroups tbody tr")
    )


def test_delete_instance_group(instance_group_prod, browser):
    tr = [
        tr for tr in browser.select_all("#tableGroups tbody tr") if "prod" in tr.text
    ][0]

    assert any(
        "Production" in group.text
        for group in browser.select_all("#tableGroups tbody tr")
    )
    tr.find_element(by=By.CSS_SELECTOR, value="[data-action=delete]").click()
    browser.select("#buttonDeleteGroup").click()
    assert not any(
        "Production" in group.text
        for group in browser.select_all("#tableGroups tbody tr")
    )
