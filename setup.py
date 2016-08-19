from setuptools import setup

requires = [ 'tornado>=3.2', 'sqlalchemy>=0.9.8' ]

setup(
    name = 'temboard',
    version = '0.0.1',
    author = 'Julien Tachoires',
    license = 'PostgreSQL',
    packages = [
            'temboardui',
            'temboardui.handlers',
            'temboardui.handlers.manage',
            'temboardui.model',
            'temboardui.plugins',
            'temboardui.plugins.dashboard',
            'temboardui.plugins.supervision',
            'temboardui.plugins.supervision.model',
            'temboardui.plugins.settings',
            'temboardui.plugins.activity'],
    scripts = ['temboard', 'temboardui/plugins/supervision/metric-aggregator'],
    include_package_data=True,
    zip_safe=False,
    url = '',
    description = 'Temboard User Interface.',
    data_files = [('/usr/share/temboard/', [
            'share/temboard.conf.sample',
            'share/ssl/temboard_CHANGEME.pem',
            'share/ssl/temboard_CHANGEME.key',
            'share/ssl/temboard_ca_certs_CHANGEME.pem',
            'share/sql/application.sql',
            'temboardui/plugins/supervision/sql/supervision.sql']
    )]
)
