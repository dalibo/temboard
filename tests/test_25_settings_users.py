import pytest

from selenium.webdriver.common.by import By


@pytest.fixture(scope="module")
def user_rick(admin_session, browser_session):
    """Go to Settings User and add user rick."""
    browser_session.select("#linkSettings").click()
    browser_session.select("a[href='/settings/users']").click()

    browser_session.select("#buttonLoadAddUserForm").click()
    browser_session.select("#inputNewUsername").send_keys("rick")
    browser_session.select("#inputEmail").send_keys("rick@test.com")
    browser_session.select("#inputPassword").send_keys("!rick0.@9")
    browser_session.select("#inputPassword2").send_keys("!rick0.@9")
    browser_session.select("#inputPhone").send_keys("+33611223344")
    browser_session.select("button.multiselect").click()
    browser_session.select("input[value='default']").click()
    browser_session.select("label[for='switchActive']").click()
    browser_session.select("label[for='switchAdmin']").click()
    browser_session.select("#submitFormAddUser").click()


def test_create_user(user_rick, browser):
    user_rick_line = [
        tr
        for tr in browser.select_all("#tableUsers tr")
        if "rick" in tr.text
    ][0]
    user_rick = user_rick_line.text.split()
    assert "rick" in user_rick
    assert "rick@test.com" in user_rick
    assert "+33611223344" in user_rick
    assert "default" in user_rick
    assert (
     "No" == user_rick_line
     .find_element(By.CSS_SELECTOR, "td[data-col='is-active']")
     .text
    )
    assert (
        "Yes" == user_rick_line
        .find_element(By.CSS_SELECTOR, "td[data-col='is-admin']")
        .text
    )


def test_update_user(user_rick, browser):
    # Find button edit for user rick
    filtered_rick_row = [
        tr
        for tr in browser.select_all("#tableUsers tr")
        if "rick" in tr.text
    ][0]
    edit_button_rick = filtered_rick_row.find_element(
        By.CSS_SELECTOR, "td button[data-original-title='Edit']"
    )
    edit_button_rick.click()

    browser.select("#inputNewUsername").clear()
    browser.select("#inputNewUsername").send_keys("rick0")
    browser.select("#inputEmail").clear()
    browser.select("#inputEmail").send_keys("rick@test.me")
    browser.select("#inputPassword").send_keys("NEW!rick0.@9")
    browser.select("#inputPassword2").send_keys("NEW!rick0.@9")
    browser.select("button.multiselect").click()
    browser.select("input[value='default']").click()
    browser.select("label[for='switchActive']").click()
    browser.select("label[for='switchAdmin']").click()
    browser.select("#submitFormUpdateUser").click()

    user_rick_line = [
        tr
        for tr in browser.select_all("#tableUsers tr")
        if "rick0" in tr.text
    ][0]
    user_rick = user_rick_line.text.split()
    assert "rick0" in user_rick
    assert "rick@test.me" in user_rick
    assert "+33611223344" in user_rick
    assert "default" not in user_rick
    assert (
        "Yes" == user_rick_line
        .find_element(By.CSS_SELECTOR, "td[data-col='is-active']")
        .text
    )
    assert (
        "No" == user_rick_line
        .find_element(By.CSS_SELECTOR, "td[data-col='is-admin']")
        .text
    )


def test_delete_user(user_rick, browser):
    # Find button delete for user rick
    filtered_rick_row = [
        tr
        for tr in browser.select_all("#tableUsers tr")
        if "rick@" in tr.text
    ][0]
    delete_button_rick = filtered_rick_row.find_element(
        By.CSS_SELECTOR, "td button[data-original-title='Delete']"
    )
    delete_button_rick.click()

    browser.find_element(
        By.XPATH, "//button[text()='Yes, delete this user']"
    ).click()

    assert len(browser.select_all("#tableUsers tr")) == 2

    assert "rick" not in [
        tr.text
        for tr in browser.select_all("#tableUsers tr")
    ]
