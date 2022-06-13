from sh import temboard


def test_start_ui(ui, browser):
    # Start UI ASAP to save some times.
    pass


def test_setproctitle_script():
    from sh import python3

    python3('ui/temboardui/toolkit/proctitle.py')


def test_setproctitle_inline():
    from sh import python3

    python3(c='import temboardui.toolkit.proctitle as pc; pc.test_main()')


def test_setproctitle_module():
    from sh import python3

    python3(m='temboardui.toolkit.proctitle')


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


def test_routes(ui_auto_configure, ui_sudo):
    assert '/login' in ui_sudo.temboard.routes()

    assert '/statements' in ui_sudo.temboard.routes('--sort')


def test_migratedb(ui_auto_configure):
    temboard('migratedb', 'check')


def test_signing_key(ui, ui_url):
    response = ui.get('/signing.key')
    response.raise_for_status()


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
