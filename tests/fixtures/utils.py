import logging
from datetime import datetime
from shutil import copy as cp

import httpx
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
)
from selenium.webdriver.common.by import By
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_delay,
    wait_chain,
    wait_fixed,
)

logger = logging.getLogger(__name__)
# Unique identifier for screenshots and log files.
session_tag = datetime.now().strftime("%H:%M")


def copy_files(candidates, targetdir):
    targetdir.mkdir(exist_ok=True, parents=True)

    for path in candidates:
        if not path.exists():
            continue

        logger.info("Saving file %s.", path)
        parent = path.parent.name
        if "agent" in parent or "ui" in parent or "temboard" in parent:
            # Avoid conflict for serve.log, auto-configure.log, etc.
            dest = targetdir / f"{parent}-{path.name}"
        else:
            dest = targetdir / path.name
        cp(path, dest)


def retry_fast(exc_type=AssertionError):
    return Retrying(
        retry=retry_if_exception_type(exc_type),
        stop=stop_after_delay(10),
        wait=wait_fixed(0.1),
    )


def retry_http():
    return retry_fast((httpx.NetworkError, OSError))


def retry_slow(exc_type=NoSuchElementException):
    # Usually to refresh a browser page.
    return Retrying(
        retry=retry_if_exception_type(exc_type),
        stop=stop_after_delay(130),
        wait=wait_chain(*[wait_fixed(5)] * 11, wait_fixed(2)),
    )


def rmtree(root):
    # Thanks to Jacques Gaudin, from
    # https://stackoverflow.com/questions/54697350/how-do-i-delete-a-directory-tree-with-pathlib.

    for path in root.iterdir():
        if path.is_dir():
            rmtree(path)
        else:
            path.unlink()

    root.rmdir()


class MultiSelect:
    # Helper for manipulating vue-multiselect components.
    def __init__(self, browser, id):
        self.browser = browser
        self.id = id

    @property
    def element(self):
        return self.browser.select(f".multiselect[aria-owns='listbox-{self.id}']")

    @property
    def trigger(self):
        return self.element.find_element(By.CSS_SELECTOR, ".multiselect__select")

    @property
    def options(self):
        return self.element.find_elements(By.CSS_SELECTOR, ".multiselect__content")

    @property
    def selected(self):
        return self.element.find_elements(By.CSS_SELECTOR, ".multiselect__tag")

    def select(self, label):
        # Toggle and select option
        for attempt in retry_fast((ElementNotInteractableException)):
            with attempt:
                self.toggle()
                for option in self.options:
                    if option.find_element(
                        By.XPATH, f"//span[contains(text(), {label!r})]"
                    ):
                        option.click()
                        return self
        raise NoSuchElementException(f"Option {label} not found")

    def unselect(self, label):
        for tag in self.selected:
            if tag.find_element(By.XPATH, f"//span[contains(text(), {label!r})]"):
                close_btn = tag.find_element(By.CSS_SELECTOR, "i")
                close_btn.click()
                return self
        raise NoSuchElementException(f"Selected option {label} not found")

    def toggle(self):
        self.trigger.click()
        return self
