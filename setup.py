# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

SETUP_KWARGS = dict(
    name='temboard',
    version='1.1',
    description='temBoard User Interface.',
    author='Julien Tachoires, Étienne BERSAC',
    license='PostgreSQL',
    scripts=['temboard'],
    install_requires=[
        'pandas>=0.15.0',
        'psycopg2>=2.5.4',
        'sqlalchemy>=0.9.8',
        'tornado>=3.2',
    ],
    include_package_data=True,
    zip_safe=False,
    url='https://github.com/dalibo/temboard/',
    data_files=[
        ('share/temboard', [
            'share/create_repository.sh',
        ]),
        ('share/temboard/sql/', [
            'share/sql/application.sql',
            'share/sql/dev-fixture.sql',
            'share/sql/monitoring.sql',
        ]),
        ('share/temboard/quickstart/', [
            'share/temboard_CHANGEME.key',
            'share/temboard_CHANGEME.pem',
            'share/temboard_ca_certs_CHANGEME.pem',
            'share/temboard.conf',
            'share/temboard.logrotate',
        ]),
        ('/usr/share/temboard', [
            'share/temboard.conf',
            'share/temboard.logrotate',
            'share/create_repository.sh',
        ]),
        ('/usr/share/temboard/sql/', [
            'share/sql/application.sql',
            'share/sql/monitoring.sql',
        ]),
        ('lib/systemd/system', ['packaging/temboard.service']),
    ]
)

setup(
    long_description=open('README.rst').read(),
    packages=find_packages(),
    **SETUP_KWARGS
)
