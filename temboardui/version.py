import re
import sys
from platform import python_version


__version__ = "7.5"


VERSION_FMT = """\
temBoard %(temboard)s
System %(distname)s %(distversion)s
Python %(python)s (%(pythonbin)s)
psycopg2 %(psycopg2)s
Tornado %(tornado)s
SQLAlchemy %(sqlalchemy)s
alembic %(alembic)s
"""


def format_version():
    return VERSION_FMT % inspect_versions()


def inspect_versions():
    from alembic import __version__ as alembic_version
    from psycopg2 import __version__ as psycopg2_version
    from tornado import version as tornado_version
    from sqlalchemy import __version__ as sqlalchemy_version

    with open('/etc/os-release') as fo:
        distinfos = parse_lsb_release(fo)

    return dict(
        temboard=__version__,
        alembic=alembic_version,
        psycopg2=psycopg2_version,
        python=python_version(),
        pythonbin=sys.executable,
        tornado=tornado_version,
        sqlalchemy=sqlalchemy_version,
        distname=distinfos['NAME'],
        distversion=distinfos['VERSION'],
    )


def parse_lsb_release(lines):
    _assignement_re = re.compile(
        r"""(?P<variable>[A-Z_]+)="(?P<value>[^"]+)"$"""
    )
    infos = dict()
    for line in lines:
        m = _assignement_re.match(line)
        if not m:
            continue
        infos[m.group('variable')] = m.group('value')
    return infos
