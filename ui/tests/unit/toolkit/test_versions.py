import sys
from textwrap import dedent


def test_os_release():
    from temboardui.toolkit.versions import parse_lsb_release

    distinfos = parse_lsb_release(
        dedent("""\
    PRETTY_NAME="Debian GNU/Linux 10 (buster)"
    NAME="Debian GNU/Linux"
    VERSION_ID="10"
    VERSION="10 (buster)"
    VERSION_CODENAME=buster
    ID=debian
    HOME_URL="https://www.debian.org/"
    SUPPORT_URL="https://www.debian.org/support"
    BUG_REPORT_URL="https://bugs.debian.org/"
    """).splitlines(True)
    )

    assert "10" == distinfos["VERSION_ID"]
    assert "10 (buster)" == distinfos["VERSION"]


def test_format_pq_version():
    from temboardui.toolkit.versions import format_pq_version

    assert "14.1" == format_pq_version(140001)
    assert "13.5" == format_pq_version(130005)
    assert "12.9" == format_pq_version(120009)
    assert "11.14" == format_pq_version(110014)
    assert "10.19" == format_pq_version(100019)
    assert "9.6.24" == format_pq_version(90624)


def test_read_libpq_version_from_ctypes(mocker):
    __import__("psycopg2.extensions")
    # Remove __libpq_version__ if any.
    mocker.patch.dict(sys.modules, [("psycopg2.extensions", object())])

    from temboardui.toolkit.versions import read_libpq_version

    assert read_libpq_version() > 90000
