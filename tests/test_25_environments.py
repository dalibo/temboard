import pytest
from fixtures.utils import retry_fast
from selenium.webdriver.common.by import By


def test_create(prod, browser):
    assert any(
        "Production" in row.text
        for row in browser.select_all("#tableEnvironments tbody tr")
    )


def test_update(prod, browser):
    tr = [
        tr
        for tr in browser.select_all("#tableEnvironments tbody tr")
        if "prod" in tr.text
    ][0]

    tr.find_element(by=By.CSS_SELECTOR, value="button[data-testid=edit]").click()
    i = browser.clickable("#inputName")
    assert i.get_attribute("value") == "prod"
    description_input = browser.select("#inputDescription")
    assert description_input.get_attribute("value") == "Production"

    description_input.send_keys(" edited")
    browser.select("button[type=submit]").click()
    assert any(
        "Production edited" in group.text
        for group in browser.select_all("#tableEnvironments tbody tr")
    )


def test_add_member(alice_member, browse_prod_members):
    browser = browse_prod_members

    for attempt in retry_fast(AssertionError):
        with attempt:
            assert (
                "alice" in browser.select("tbody tr:nth-child(1) td:nth-child(1)").text
            )


def test_remove_member(alice_member, browse_prod_members):
    browser = browse_prod_members
    browser.select("tbody tr:nth-child(1) button").click()
    username = browser.select(".modal-body strong").text
    assert username.startswith("a")  # admin or alice
    browser.select("#buttonDelete").click()
    browser.absent("tbody tr:nth-child(2)")
    assert username not in browser.select("tbody").text


def test_delete(prod, browse_settings_environments):
    browser = browse_settings_environments

    tr = [
        tr
        for tr in browser.select_all("#tableEnvironments tbody tr")
        if "prod" in tr.text
    ][0]

    tr.find_element(by=By.CSS_SELECTOR, value="[data-testid=delete]").click()
    browser.select("#buttonDelete").click()
    browser.absent("#tableEnvironments tbody tr:nth-child(2)")
    assert "prod" not in browser.select("#tableEnvironments tbody").text


@pytest.fixture()
def browse_settings_environments(browser, ui_url, admin_session):
    browser.get(ui_url + "/settings/environments")
    return browser


@pytest.fixture()
def browse_prod_members(prod, browser, ui_url):
    browser.get(ui_url + "/settings/environments")
    # Click prod members link.
    browser.select("tr:nth-child(2) a[data-testid=members]").click()
    return browser


@pytest.fixture(scope="module")
def alice_member(alice, prod, browser_session, ui_url):
    """Add alice to prod environment"""
    browser = browser_session
    browser.get(ui_url + "/settings/environments")
    # Click prod members link.
    browser.select("tr:nth-child(2) a[data-testid=members]").click()
    assert "prod" in browser.select("#members-app h5").text
    # Click Add Member in prod members page.
    browser.select("button[data-testid=add]").click()
    browser.clickable(".modal-body input[type=search]").send_keys("al")
    # Ensure there is a single member.
    browser.absent("[data-testid=members] li:nth-child(2)")
    btn = browser.clickable(".modal-body [data-testid=members] li:first-child button")
    assert "alice" in btn.text
    btn.click()
    browser.hidden("#modalAddMember")


@pytest.fixture(scope="module")
def alice(admin_session, browser_session):
    b = browser_session
    b.select("#linkSettings").click()
    b.select("a[href='/settings/users']").click()
    b.select("button[data-bs-target='#modalEditUser']").click()
    b.clickable("input[placeholder='Username']").send_keys("alice")
    b.select("input[placeholder='Password']").send_keys("totoT0T0")
    b.select("input[placeholder='Confirm password']").send_keys("totoT0T0")
    b.select("button[type=submit]").click()
    b.hidden("#modalEditUser")


@pytest.fixture(scope="module")
def prod(browser_session, ui_url, admin_session):
    browser = browser_session
    browser.get(ui_url + "/settings/environments")
    browser.select("button[data-testid=new]").click()
    browser.clickable("#inputName").send_keys("prod")
    browser.select("#inputDescription").send_keys("Production")
    browser.select("button[type=submit]").click()
