import csv

from sh import temboard


def test_start_ui(agent, ui, browser):
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


def test_runtask(ui_auto_configure):
    out = temboard("runtask", "?")

    assert '\ncollector\n' in out


def test_signing_key(ui):
    response = ui.get('/signing.key')
    response.raise_for_status()


def test_apikey_lifecycle(ui_auto_configure, ui_sudo):
    out = ui_sudo.temboard.apikey.create()
    reader = csv.reader(out)

    header = next(reader)
    assert 'Id' in header
    assert 'Secret' in header
    assert 'Comment' in header
    assert 'Expiration' in header

    key = next(reader)

    out = ui_sudo.temboard.apikey.list()
    reader = csv.reader(out)
    for row in reader:
        if row[0] == key[0]:
            break
    else:
        assert False, "Key not listed"

    ui_sudo.temboard.apikey.delete(key[0])
    out = ui_sudo.temboard.apikey.list()
    secret = key[1]
    assert secret not in out

    ui_sudo.temboard.apikey.purge()


def test_proctitle(ui):
    if b'sudo' in ui.proc.cmd[0]:  # CI case
        ppid = ui.proc.pid
        with open(f"/proc/{ppid}/task/{ppid}/children") as fo:
            children = fo.read()
        pid = int(children)
    else:  # dev case
        pid = ui.proc.pid

    with open(f"/proc/{pid}/cmdline") as fo:
        cmdline = fo.read()

    assert cmdline.startswith('temboard: web')

    with open(f"/proc/{pid}/task/{pid}/children") as fo:
        children = fo.read()
    children = children.split()

    for childpid in children:
        with open(f"/proc/{childpid}/cmdline") as fo:
            cmdline = fo.read()

        assert cmdline.startswith('temboard: ')

        assert ': worker' in cmdline or ': scheduler' in cmdline


def test_autossl(ui):
    http_url = ui.base_url.copy_with(scheme='http')
    response = ui.get(http_url)

    assert 301 == response.status_code
    assert response.headers['location'].startswith('https://')


def test_login_logout(browser, ui, ui_url):
    browser.get(ui_url + '/')

    browser.select("#inputUsername").send_keys("admin")
    browser.select("#inputPassword").send_keys("admin")
    browser.select("button[type=submit]").click()

    # Assert link to instances exists.
    browser.select("a[href='/settings/instances']")

    browser.select("li.nav-item.dropdown a").click()
    browser.select("a[href='/logout']").click()
