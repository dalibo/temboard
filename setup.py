from setuptools import setup

requires = [
    'pandas>=0.15.0',
    'psycopg2>=2.5.4',
    'sqlalchemy>=0.9.8',
    'tornado>=3.2',
]

setup(
    name='temboard',
    version='0.0.1',
    author='Julien Tachoires',
    license='PostgreSQL',
    packages=[
        'temboardui',
        'temboardui.handlers',
        'temboardui.handlers.manage',
        'temboardui.model',
        'temboardui.plugins',
        'temboardui.plugins.dashboard',
        'temboardui.plugins.supervision',
        'temboardui.plugins.supervision.model',
        'temboardui.plugins.settings',
        'temboardui.plugins.activity'
    ],
    scripts=['temboard'],
    install_requires=requires,
    include_package_data=True,
    zip_safe=False,
    url='',
    description='temBoard User Interface.',
    data_files=[('share/temboard/', [
        'share/sql/application.sql',
        'share/ssl/temboard_CHANGEME.key',
        'share/ssl/temboard_CHANGEME.pem',
        'share/ssl/temboard_ca_certs_CHANGEME.pem',
        'share/temboard.conf.sample',
        'share/temboard.logrotate'
        'temboardui/plugins/supervision/sql/supervision.sql',
    ])])
