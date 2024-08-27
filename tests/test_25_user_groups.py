import pytest
from selenium.webdriver.common.by import By


@pytest.fixture(scope="module")
def browse_settings_user_groups(browser_session, ui_url, admin_session):
    browser_session.get(ui_url + "/settings/groups/role")


@pytest.fixture(scope="module")
def user_group_dev(browse_settings_user_groups, browser_session):
    browser_session.select("#buttonLoadAddGroupForm").click()
    browser_session.select("#inputNewGroupname").send_keys("dev")
    browser_session.select("#inputDescription").send_keys("Developers")
    browser_session.select("button[type=submit]").click()


def test_create_user_group(user_group_dev, browser):
    assert any(
        "Developers" in group.text
        for group in browser.select_all("#tableGroups tbody tr")
    )


def test_update_user_group(user_group_dev, browser):
    tr = [tr for tr in browser.select_all("#tableGroups tbody tr") if "dev" in tr.text][
        0
    ]

    tr.find_element(by=By.CSS_SELECTOR, value="[data-action=edit]").click()
    assert browser.select("#inputNewGroupname").get_attribute("value") == "dev"
    description_input = browser.select("#inputDescription")
    assert description_input.get_attribute("value") == "Developers"

    description_input.send_keys(" and testers")
    browser.select("button[type=submit]").click()
    assert any(
        "Developers and testers" in group.text
        for group in browser.select_all("#tableGroups tbody tr")
    )


def test_delete_user_group(user_group_dev, browser):
    tr = [tr for tr in browser.select_all("#tableGroups tbody tr") if "dev" in tr.text][
        0
    ]

    assert any(
        "Developers" in group.text
        for group in browser.select_all("#tableGroups tbody tr")
    )
    tr.find_element(by=By.CSS_SELECTOR, value="[data-action=delete]").click()
    browser.clickable("#buttonDelete").click()
    assert not any(
        "Developers" in group.text
        for group in browser.select_all("#tableGroups tbody tr")
    )
