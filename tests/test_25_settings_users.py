import pytest
from fixtures.utils import MultiSelect
from selenium.webdriver.common.by import By


@pytest.fixture(scope="module")
def user_rick(admin_session, browser_session):
    """Go to Settings User and add user rick."""
    browser_session.select("#linkSettings").click()
    browser_session.select("a[href='/settings/users']").click()

    browser_session.select("#buttonLoadAddUserForm").click()
    browser_session.select("input[placeholder='Username']").send_keys("rick")
    browser_session.select("input[placeholder='Email']").send_keys("rick@test.com")
    browser_session.select("input[placeholder='Password']").send_keys("!rick0.@9")
    browser_session.select("input[placeholder='Confirm password']").send_keys(
        "!rick0.@9"
    )
    browser_session.select("input[placeholder='Phone']").send_keys("+33611223344")
    multiselect = MultiSelect(browser_session, "groups")
    multiselect.toggle().select("default")
    browser_session.select("label[for='switchActive']").click()
    browser_session.select("label[for='switchAdmin']").click()
    browser_session.select("button[type=submit]").click()


def test_create_user(user_rick, browser):
    user_rick_line = [
        tr for tr in browser.select_all("#tableUsers tr") if "rick" in tr.text
    ][0]
    user_rick = user_rick_line.text.split()
    assert "rick" in user_rick
    assert "rick@test.com" in user_rick
    assert "+33611223344" in user_rick
    assert "default" in user_rick
    assert (
        "No"
        == user_rick_line.find_element(By.CSS_SELECTOR, "td[data-col='is-active']").text
    )
    assert (
        "Yes"
        == user_rick_line.find_element(By.CSS_SELECTOR, "td[data-col='is-admin']").text
    )


def test_update_user(user_rick, browser):
    # Find button edit for user rick
    filtered_rick_row = [
        tr for tr in browser.select_all("#tableUsers tr") if "rick" in tr.text
    ][0]
    edit_button_rick = filtered_rick_row.find_element(
        By.CSS_SELECTOR, "td button[title='Edit']"
    )
    edit_button_rick.click()

    browser.select("input[placeholder='Username']").clear()
    browser.select("input[placeholder='Username']").send_keys("rick0")
    browser.select("input[placeholder='Email']").clear()
    browser.select("input[placeholder='Email']").send_keys("rick@test.me")
    browser.select("input[placeholder='Password']").send_keys("NEW!rick0.@9")
    browser.select("input[placeholder='Confirm password']").send_keys("NEW!rick0.@9")

    multiselect = MultiSelect(browser, "groups")
    multiselect.unselect("default")
    browser.select("label[for='switchActive']").click()
    browser.select("label[for='switchAdmin']").click()
    browser.select("button[type=submit]").click()

    user_rick_line = [
        tr for tr in browser.select_all("#tableUsers tr") if "rick0" in tr.text
    ][0]
    user_rick = user_rick_line.text.split()
    assert "rick0" in user_rick
    assert "rick@test.me" in user_rick
    assert "+33611223344" in user_rick
    assert "default" not in user_rick
    assert (
        "Yes"
        == user_rick_line.find_element(By.CSS_SELECTOR, "td[data-col='is-active']").text
    )
    assert (
        "No"
        == user_rick_line.find_element(By.CSS_SELECTOR, "td[data-col='is-admin']").text
    )


def test_delete_user(user_rick, browser):
    # Find button delete for user rick
    filtered_rick_row = [
        tr for tr in browser.select_all("#tableUsers tr") if "rick@" in tr.text
    ][0]
    delete_button_rick = filtered_rick_row.find_element(
        By.CSS_SELECTOR, "td button[title='Delete']"
    )
    delete_button_rick.click()

    browser.select("#buttonDelete").click()

    assert len(browser.select_all("#tableUsers tr")) == 2

    assert "rick" not in [tr.text for tr in browser.select_all("#tableUsers tr")]
