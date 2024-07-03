import pytest
from selenium.webdriver.support.select import Select


@pytest.fixture
def browse_pgconf(browse_instance, browser):
    """Go to Configuration tab of current instance."""
    browser.select("div.sidebar a.pgconf").click()


def test_category_selector(browse_pgconf, browser):
    # Ensure some categories are listed
    browser.select("#selectConfCat option:nth-child(10)")

    selected_category = browser.select("#selectConfCat option[selected]").text
    current_category = browser.select(".card-header").text
    assert selected_category == current_category

    category_selector = Select(browser.select("#selectConfCat"))
    category_selector.select_by_visible_text("Error Handling")
    current_category = browser.select(".card-header").text
    assert "Error Handling" == current_category


def test_search(browse_pgconf, browser):
    # Ensure only one category is shown.
    cards = browser.select_all(".main .card")
    assert 1 == len(cards)

    browser.select("#inputSearchSettings").send_keys("archive")
    browser.select("#buttonSearchSettings").click()

    # Ensure several categories matches. Number varies accross PostgreSQL
    # version.
    browser.mincount(".main .card", 2)

    badges = browser.select_all(".main .card tr td:nth-child(1)")
    for badge in badges:
        assert "archive" in badge.text

    browser.select("#buttonResetSearch").click()
    assert not browser.select("#inputSearchSettings").get_attribute("value")


def test_boolean(browse_pgconf, browser, psql):
    param = "check_function_bodies"
    browser.select("#inputSearchSettings").send_keys(param)
    browser.select("#buttonSearchSettings").click()

    assert browser.select(".input-setting input[type='checkbox']").get_attribute(
        "checked"
    )

    out = psql("-Abt", c=f"SHOW {param};")
    assert "on" == out.strip()

    browser.absent(f"#buttonResetDefault_{param}")

    browser.select(".input-setting input[type=checkbox").click()
    # Ensure checkbox is unchecked
    assert not browser.select(".input-setting input[type='checkbox']").get_attribute(
        "checked"
    )

    browser.select(".main form button[type=submit]").click()

    # Ensure Reset button appears
    browser.select(f"#buttonResetDefault_{param}")

    out = psql("-Abt", c=f"SHOW {param};")
    assert "off" == out.strip()


def test_integer(browse_pgconf, browser, psql):
    param = "autovacuum_vacuum_threshold"
    browser.select("#inputSearchSettings").send_keys(param)
    browser.select("#buttonSearchSettings").click()

    input_ = browser.select(f"input[name={param}]")
    assert "50" == input_.get_attribute("value")

    out = psql("-Abt", c=f"SHOW {param};")
    assert "50" == out.strip()

    browser.absent(f"#buttonResetDefault_{param}")

    input_.send_keys(browser.Keys.BACKSPACE)
    input_.send_keys(browser.Keys.BACKSPACE)
    input_.send_keys("100")

    browser.select(".main form button[type=submit]").click()

    # Ensure Reset button appears
    browser.select(f"#buttonResetDefault_{param}")

    out = psql("-Abt", c=f"SHOW {param};")
    assert "100" == out.strip()


def test_bytes(browse_pgconf, browser, psql):
    param = "maintenance_work_mem"
    browser.select("#inputSearchSettings").send_keys(param)
    browser.select("#buttonSearchSettings").click()

    input_ = browser.select(f"input[name={param}]")
    assert "64MB" == input_.get_attribute("value")

    out = psql("-Abt", c=f"SHOW {param};")
    assert "64MB" == out.strip()

    browser.absent(f"#buttonResetDefault_{param}")

    input_.send_keys(browser.Keys.BACKSPACE)  # 64M
    input_.send_keys(browser.Keys.BACKSPACE)  # 64
    input_.send_keys(browser.Keys.BACKSPACE)  # 6
    input_.send_keys(browser.Keys.BACKSPACE)
    input_.send_keys("128MB")

    browser.select(".main form button[type=submit]").click()

    # Ensure Reset button appears
    browser.select(f"#buttonResetDefault_{param}")

    out = psql("-Abt", c=f"SHOW {param};")
    assert "128MB" == out.strip()


def test_enum(browse_pgconf, browser, psql):
    param = "log_error_verbosity"
    browser.select("#inputSearchSettings").send_keys(param)
    browser.select("#buttonSearchSettings").click()

    out = psql("-Abt", c=f"SHOW {param};")
    current_value = out.strip()
    assert "default" == current_value

    enum_selector = Select(browser.select(f"select[name={param}]"))
    selected = enum_selector.first_selected_option.get_attribute("value")
    assert current_value == selected

    browser.absent(f"#buttonResetDefault_{param}")

    enum_selector.select_by_value("verbose")

    browser.select(".main form button[type=submit]").click()

    out = psql("-Abt", c=f"SHOW {param};")
    assert "verbose" == out.strip()

    browser.select(f"#buttonResetDefault_{param}")
