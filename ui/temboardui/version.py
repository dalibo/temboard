import sys
from platform import python_version

__version__ = "9.0.0"


# This output is parsed by tests/conftest.py::pytest_report_header.
VERSION_FMT = """\
temBoard %(temboard)s (%(temboardbin)s)
System %(distname)s %(distversion)s
Python %(python)s (%(pythonbin)s)
cryptography %(cryptography)s
Tornado %(tornado)s
Flask %(flask)s
libpq %(libpq)s
psycopg2 %(psycopg2)s
SQLAlchemy %(sqlalchemy)s
"""


def format_version():
    return VERSION_FMT % inspect_versions()


def inspect_versions():
    import cryptography
    import flask
    import psycopg2
    import sqlalchemy
    import tornado

    from .toolkit.versions import format_pq_version, read_distinfo, read_libpq_version

    distinfos = read_distinfo()

    return dict(
        cryptography=cryptography.__version__,
        distname=distinfos["NAME"],
        distversion=distinfos.get("VERSION", "n/a"),
        flask=flask.__version__,
        libpq=format_pq_version(read_libpq_version()),
        psycopg2=psycopg2.__version__,
        python=python_version(),
        pythonbin=sys.executable,
        sqlalchemy=sqlalchemy.__version__,
        temboard=__version__,
        temboardbin=sys.argv[0],
        tornado=tornado.version,
    )
