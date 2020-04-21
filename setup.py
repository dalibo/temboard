# -*- coding: utf-8 -*-

import os
import sys

from setuptools import setup, find_packages, __version__ as setuptoolsv


# Load version number
__version__ = None
setup_path = os.path.dirname(os.path.realpath(__file__))
exec(open(os.path.join(setup_path, 'temboardui', 'version.py'), 'r').read())

if setuptoolsv < '1.0':
    __version__ = __version__.replace('+', '.')

# Accept Tornado 5.X on Python 2.7.9+
BLEEDING_EDGE_TORNADO = '4.5' if sys.version_info < (2, 7, 9) else '6'


SETUP_KWARGS = dict(
    name='temboard',
    version=__version__,  # noqa, imported by execfile.
    description='temBoard User Interface.',
    author='Julien Tachoires, Étienne BERSAC',
    license='PostgreSQL',
    install_requires=[
        'alembic',
        'futures',
        'python-dateutil>=1.5',
        # There is no hard dependency on psycopg2 to allow using
        # psycopg2-binary instead. psycopg2 is not provided by psycopg2-binary
        # and there is no way to state an OR dependency in Python. It's up to
        # the user or package manager to ensure psycopg2 dependency. See
        # documentation.
        'sqlalchemy>=0.9.8',
        'tornado>=3.2,<' + BLEEDING_EDGE_TORNADO,
    ],
    include_package_data=True,
    zip_safe=False,
    url='https://github.com/dalibo/temboard/',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 2 :: Only",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: System :: Monitoring",
    ],
    data_files=[
        ('share/temboard', [
            'share/auto_configure.sh',
            'share/create_repository.sh',
            'share/purge.sh',
        ]),
        ('share/temboard/sql/', [
            'share/sql/dev-fixture.sql',
            'share/sql/upgrade-monitoring-purge-instances.sql',
        ]),
        ('share/temboard/quickstart/', [
            'share/temboard_CHANGEME.key',
            'share/temboard_CHANGEME.pem',
            'share/temboard_ca_certs_CHANGEME.pem',
            'share/temboard.conf',
            'share/temboard.logrotate',
        ]),
        ('lib/systemd/system', ['packaging/temboard.service']),
    ],
    entry_points={
        'console_scripts': [
            'temboard = temboardui.__main__:main',
            'temboard-migratedb = temboardui.migratedb:main',
        ],
    },
)


if __name__ == '__main__':
    setup(
        long_description=open('README.rst').read(),
        packages=find_packages(),
        **SETUP_KWARGS
    )
