import pytest
from fixtures.utils import MultiSelect
from selenium.webdriver.common.by import By


@pytest.fixture(scope="module")
def user_rick(admin_session, browser_session):
    """Go to Settings User and add user rick."""
    b = browser_session
    b.select("#linkSettings").click()
    b.select("a[href='/settings/users']").click()

    b.select("#buttonNewUser").click()
    # Wait form to be interactive
    b.clickable("input[placeholder='Username']").send_keys("rick")
    b.select("input[placeholder='Email']").send_keys("rick@test.com")
    b.select("input[placeholder='Password']").send_keys("!rick0.@9")
    b.select("input[placeholder='Confirm password']").send_keys("!rick0.@9")
    b.select("input[placeholder='+33...']").send_keys("+33611223344")
    multiselect = MultiSelect(b, "groups")
    multiselect.select("default")
    b.select("label[for='switchActive']").click()
    b.select("label[for='switchAdmin']").click()
    b.select("#modalEditUser button[type=submit]").click()
    b.hidden("#modalEditUser")


def test_create_user(user_rick, browser):
    user_rick_line = [
        tr for tr in browser.select_all("#tableUsers tr") if "rick" in tr.text
    ][0]
    user_rick = user_rick_line.text.split()
    assert "rick" in user_rick
    assert "rick@test.com" in user_rick
    assert "+33611223344" in user_rick
    assert "default" in user_rick
    assert "Inactive" in user_rick
    assert "Admin" in user_rick


def test_update_user(user_rick, browser):
    # Find button edit for user rick
    filtered_rick_row = [
        tr for tr in browser.select_all("#tableUsers tr") if "rick" in tr.text
    ][0]
    edit_button_rick = filtered_rick_row.find_element(
        By.CSS_SELECTOR, "td button[title='Edit']"
    )
    edit_button_rick.click()
    browser.clickable("input[placeholder='Username']").clear()
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
    browser.hidden("#modalEditUser")

    user_rick_line = [
        tr for tr in browser.select_all("#tableUsers tr") if "rick0" in tr.text
    ][0]
    user_rick = user_rick_line.text.split()
    assert "rick0" in user_rick
    assert "rick@test.me" in user_rick
    assert "+33611223344" in user_rick
    assert "default" not in user_rick
    assert "Active" in user_rick
    assert "User" in user_rick


def test_delete_user(user_rick, browser):
    initial_rows = browser.select_all("#tableUsers tbody tr")
    # Find button delete for user rick
    filtered_rick_row = [tr for tr in initial_rows if "rick@" in tr.text][0]
    delete_button_rick = filtered_rick_row.find_element(
        By.CSS_SELECTOR, "td button[title='Delete']"
    )
    delete_button_rick.click()

    browser.select("#buttonDelete").click()

    assert len(browser.select_all("#tableUsers tbody tr")) < len(initial_rows)

    assert "rick" not in [tr.text for tr in browser.select_all("#tableUsers tr")]
