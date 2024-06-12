import json

import pytest
from sh import temboard, ErrorReturnCode


def test_query_agent(ui_auto_configure, agent):
    client = temboard.bake("query-agent", _tty_in=True)

    # Error
    url = f"{agent.base_url}/bad-path"
    with pytest.raises(ErrorReturnCode):
        client(url)

    # GET
    url = f"{agent.base_url}/discover"
    out = client(url)
    data = json.loads(str(out))
    assert 'postgres' in data


def test_about_temboard(admin_session, browser, ui_url):
    browser.get(ui_url + '/about')
    metadata = browser.select('#metadata').text
    assert "Version" in metadata
    browser.select("#buttonCopy").click()


def test_web_register(
        registered_agent, agent_conf, browser, pg_version, ui_url):
    browser.get(ui_url + '/settings/instances')
    port = agent_conf.get('temboard', 'port')

    server, postgres, agent = range(1, 4)
    fmt = "table#tableInstances tr td:nth-child({col})".format

    assert 'default' in browser.select(fmt(col=server)).text
    assert port in browser.select(fmt(col=agent)).text
    assert pg_version in browser.select(fmt(col=postgres)).text


def test_about_instance(registered_agent, agent_conf, browser, ui_url):
    port = agent_conf.get('temboard', 'port')
    browser.get(ui_url + '/server/0.0.0.0/' + port + '/about')
    browser.select('.postgres .version')
    browser.select('.temboard .plugins .pgconf')


def test_edit_instance(registered_agent, browser, ui_url):
    browser.get(ui_url + '/settings/instances')
    browser.select("td button.buttonEdit").click()
    browser.select("#inputNotify").click()
    comment = browser.select("#inputComment").get_attribute('value')
    assert "Registered by tests." == comment
    browser.select("#buttonSubmit").click()


def test_download_inventory(registered_agent, browser):
    browser.select("#linkSettings").click()
    download = browser.select("#buttonDownload")

    download.click()
    browser.select("#buttonDownload")  # Ensure page is still present.

    *_, filename = browser.list_download_filenames()
    assert filename.endswith('.csv')

    csv = browser.fetch_remote_file(filename).decode('utf-8')
    header, instance = csv.splitlines()

    assert "Hostname;Port" in header
    assert "default" in instance
