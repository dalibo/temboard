import httpx
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException
from tenacity import (
    Retrying, retry_if_exception_type, stop_after_delay,
    wait_chain, wait_fixed,
)


# Unique identifier for screenshots and log files.
session_tag = datetime.now().strftime('%H:%M')


def retry_fast(exc_type=AssertionError):
    return Retrying(
        retry=retry_if_exception_type(exc_type),
        stop=stop_after_delay(10),
        wait=wait_fixed(.1),
    )


def retry_http():
    return retry_fast((httpx.NetworkError, OSError))


def retry_slow(exc_type=NoSuchElementException):
    # Usually to refresh a browser page.
    return Retrying(
        retry=retry_if_exception_type(exc_type),
        stop=stop_after_delay(130),
        wait=wait_chain(
            *[wait_fixed(5)] * 11,
            wait_fixed(2),
        ),
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
