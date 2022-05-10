def test_web_register(
        registered_agent, agent_conf, browser, pg_version, ui_url):
    browser.get(ui_url + '/settings/instances')
    port = agent_conf.get('temboard', 'port')

    agent, hostname, pg_version_col, pg_port_col, pgdata, groups = range(1, 7)
    fmt = "table#tableInstances tr td:nth-child({col})".format

    assert port in browser.select(fmt(col=agent)).text
    assert pg_version in browser.select(fmt(col=pg_version_col)).text
    assert 'default' in browser.select(fmt(col=groups)).text
