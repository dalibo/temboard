# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import subprocess

try:
    # pip install mode
    with open('PKG-INFO') as fo:
        for line in fo:
            if not line.startswith('Version: '):
                continue
            VERSION = line.replace('Version: ', '').strip()
            break
except IOError:
    try:
        # Release mode
        # git describe returns version[-count-gsha1].
        version, count, sha = (
            subprocess.check_output(["git", "describe", "--tags"])
            .strip().decode() + '--'
        ).split('-', 3)[:3]
    except Exception:
        VERSION = '0'
    else:
        VERSION = version
        if count:
            VERSION += '.dev%s' % (count,)

setup(
    name='temboard',
    version=VERSION,
    description='temBoard User Interface.',
    long_description=open('README.rst').read(),
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
    data_files=[
        ('share/temboard/', [
            'share/sql/application.sql',
            'share/sql/dev-fixture.sql',
            'share/ssl/temboard_CHANGEME.key',
            'share/ssl/temboard_CHANGEME.pem',
            'share/ssl/temboard_ca_certs_CHANGEME.pem',
            'share/temboard.conf.sample',
            'share/temboard.logrotate',
            'temboardui/plugins/monitoring/sql/monitoring.sql',
        ]),
        ('lib/systemd/system', ['temboard.service']),
    ])
