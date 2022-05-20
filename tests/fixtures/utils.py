import httpx
from tenacity import (
    Retrying, retry_if_exception_type, wait_fixed, stop_after_delay,
)


def retry_http():
    return Retrying(
        retry=retry_if_exception_type((httpx.NetworkError, OSError)),
        stop=stop_after_delay(10),
        wait=wait_fixed(.1),
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
