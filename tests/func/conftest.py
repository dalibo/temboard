import os

import pytest
from selenium.webdriver import Remote
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


@pytest.fixture(scope='session')
def selenium():
    executor = os.environ.get('SELENIUM', 'http://localhost:4444') + '/wd/hub'
    driver = Remote(
        command_executor=executor,
        desired_capabilities=DesiredCapabilities.FIREFOX.copy(),
    )
    driver.implicitly_wait(3)
    yield driver
    driver.quit()
