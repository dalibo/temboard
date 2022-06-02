import pytest
from sh import temboard, ErrorReturnCode


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


def test_migratedb_no_database(ui_sudo):
    with pytest.raises(ErrorReturnCode):
        ui_sudo.temboard.migratedb.check()


# Next tests of this module has auto_configure.sh executed.


def test_routes(ui_auto_configure, ui_sudo, ):
    assert '/login' in ui_sudo.temboard.routes()

    assert '/statements' in ui_sudo.temboard.routes('--sort')


def test_auto_configure(ui_auto_configure):
    temboard('migratedb', 'check')


def test_login_logout(browser, ui, ui_url):
    browser.get(ui_url + '/')

    browser.select("#inputUsername").send_keys("admin")
    browser.select("#inputPassword").send_keys("admin")
    browser.select("button[type=submit]").click()

    # Assert link to instances exists.
    browser.select("a[href='/settings/instances']")

    browser.select("li.nav-item.dropdown a").click()
    browser.select("a[href='/logout']").click()


def test_runtask(ui):
    out = temboard("runtask", "?")

    assert '\ncollector\n' in out
