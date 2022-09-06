from time import sleep

from selenium.webdriver.common.keys import Keys


def test_dashboard(browser, registered_agent, ui_url):
    browser.get(ui_url)  # Goto home
    browser.select("a.instance-link").click()  # Click first instance

    sleep(2)  # Dashboard tempo is 2 seconds.

    assert browser.select("span#os_version").text

    cpu, percent = browser.select("#total-cpu").text.split()
    assert '%' == percent
    assert 0 <= int(cpu) <= 100

    browser.hover("#cpu-info")
    sleep(.1)
    tooltip = browser.select("#cpu-info").get_attribute("aria-describedby")
    cpuinfo = browser.select(f"#{tooltip}").text
    assert 'CPU @' in cpuinfo

    # Vanish tooltip
    browser.hover("body")
    sleep(.1)
    browser.absent(f"#{tooltip}")

    memory, percent = browser.select("#total-memory").text.split()
    assert '%' == percent
    assert int(memory) > 1

    memory, unit = browser.select("#memory").text.split()
    assert unit.endswith('B')
    assert float(memory) > 1

    assert browser.select("#pg_start_time").text
    assert 2 == int(browser.select("#nb_db").text)
    db_size, unit = browser.select("b#size").text.split()
    assert 'B' in unit
    assert int(db_size) > 1

    hitratio, percent = browser.select("#total-hit").text.split()
    assert '%' == percent
    assert int(hitratio) > 0

    current, maximum = browser.select("#total-sessions").text.split(' / ')
    assert int(current) > 0
    assert '100' == maximum

    assert browser.select("canvas#chart-loadaverage")
    loadavg = browser.select("#loadaverage").text
    assert float(loadavg) > 0

    assert browser.select("canvas#chart-tps")
    commits = browser.select("#tps_commit").text
    assert int(commits) >= 0
    rollbacks = browser.select("#tps_rollback").text
    assert int(rollbacks) >= 0

    browser.select("a.fullscreen").click()  # Go fullscreen

    browser.select("body").send_keys(Keys.ESCAPE)  # Exit fullscreen
