import pytest
from sh import temboard, temboard_migratedb, ErrorReturnCode


def test_temboard_version():
    out = temboard('--version')

    assert 'temBoard ' in out
    assert 'Python ' in out
    assert 'Tornado ' in out
    assert 'psycopg2 ' in out
    assert 'libpq ' in out
    assert 'SQLAlchemy ' in out


def test_temboard_help():
    temboard('--help')


def test_migratedb_no_database():
    with pytest.raises(ErrorReturnCode):
        temboard_migratedb('check')


def test_auto_configure(ui_auto_configure):
    temboard_migratedb('check')


def test_login_logout(browser, ui, ui_url):
    browser.get(ui_url + '/')

    browser.select("#inputUsername").send_keys("admin")
    browser.select("#inputPassword").send_keys("admin")
    browser.select("button[type=submit]").click()

    # Assert link to instances exists.
    browser.select("a[href='/settings/instances']")

    browser.select("li.nav-item.dropdown a").click()
    browser.select("a[href='/logout']").click()
