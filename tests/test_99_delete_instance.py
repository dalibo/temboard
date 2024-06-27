import pytest


@pytest.fixture(scope="module")
def browse_settings_instance(browse_instance, browser_session):
    """Go to Settings tab of current instance."""
    browser_session.select("#linkSettings").click()
    browser_session.select("ul.list-group a[href='/settings/instances']").click()


def test_delete_instance(browser, browse_settings_instance, agent_conf):
    browser.select("td button.buttonDelete").click()
    browser.select("#modalDeleteInstance button#buttonDelete").click()
    port = agent_conf.get("temboard", "port")
    # Check the instance has been deleted
    assert all(
        f"0.0.0.0:{port}" not in tr.text
        for tr in browser.select_all("#tableInstances tbody tr")
    )
