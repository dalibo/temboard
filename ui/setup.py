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
# Accept Tornado 6.X on Python 3+
BLEEDING_EDGE_TORNADO = '7'
if sys.version_info < (2, 7, 9):
    BLEEDING_EDGE_TORNADO = '4.5'
elif sys.version_info < (3,):
    BLEEDING_EDGE_TORNADO = '6'

install_requires = [
    'cryptography',
    'flask',
    'python-dateutil>=1.5',
    # There is no hard dependency on psycopg2 to allow using
    # psycopg2-binary instead. psycopg2 is not provided by psycopg2-binary
    # and there is no way to state an OR dependency in Python. It's up to
    # the user or package manager to ensure psycopg2 dependency. See
    # documentation.
    'sqlalchemy>=0.9.8',
    'tornado>=3.2,<' + BLEEDING_EDGE_TORNADO,
    'future',
]

if sys.version_info < (3,):
    install_requires.append('futures')

SETUP_KWARGS = dict(
    name='temboard',
    version=__version__,  # noqa, imported by execfile.
    description='temBoard User Interface.',
    author='Dalibo',
    author_email='contact@dalibo.com',
    license='PostgreSQL',
    url='https://labs.dalibo.com/temboard',
    classifiers=[
        "Intended Audience :: System Administrators",
        "License :: OSI Approved",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: System :: Monitoring",
    ],
    install_requires=install_requires,
    include_package_data=True,
    zip_safe=False,
    data_files=[
        ('share/temboard', [
            'share/auto_configure.sh',
            'share/create_repository.sh',
            'share/purge.sh',
        ]),
        ('share/temboard/sql/', [
            'share/sql/dev-fixture.sql',
            'share/sql/upgrade-monitoring-purge-instances.sql',
            'share/sql/reassign.sql',
        ]),
        ('share/temboard/quickstart/', [
            'share/temboard_CHANGEME.key',
            'share/temboard_CHANGEME.pem',
            'share/temboard_ca_certs_CHANGEME.pem',
            'share/temboard.conf',
        ]),
        ('lib/systemd/system', ['packaging/temboard.service']),
    ],
    entry_points={
        'console_scripts': [
            'temboard = temboardui.__main__:main',
        ],
        'temboardui.plugins': [
            'activity = temboardui.plugins.activity:ActivityPlugin',
            'dashboard = temboardui.plugins.dashboard:DashboardPlugin',
            'maintenance = temboardui.plugins.maintenance:MaintenancePlugin',
            'monitoring = temboardui.plugins.monitoring:MonitoringPlugin',
            'pgconf = temboardui.plugins.pgconf:PGConfPlugin',
            'statements = temboardui.plugins.statements:StatementsPlugin',
        ]
    },
)


if __name__ == '__main__':
    setup(
        long_description=open(setup_path + '/README.md').read(),
        long_description_content_type='text/markdown',
        packages=find_packages(),
        **SETUP_KWARGS
    )
