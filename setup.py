# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='temboard',
    version='0.0.1',
    author='Julien Tachoires, Étienne BERSAC',
    license='PostgreSQL',
    packages=find_packages(),
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
    description='temBoard User Interface.',
    data_files=[('share/temboard/', [
        'share/sql/application.sql',
        'share/ssl/temboard_CHANGEME.key',
        'share/ssl/temboard_CHANGEME.pem',
        'share/ssl/temboard_ca_certs_CHANGEME.pem',
        'share/temboard.conf.sample',
        'share/temboard.logrotate',
        'temboardui/plugins/supervision/sql/supervision.sql'
    ])])
