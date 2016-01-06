from setuptools import setup

requires = [ 'tornado>=3.2', 'sqlalchemy>=0.9.8' ]

setup(
    name = 'ganesh',
    version = '0.0.1',
    author = 'Julien Tachoires',
    license = 'PostgreSQL',
    packages = [
            'ganeshwebui',
            'ganeshwebui.handlers',
            'ganeshwebui.handlers.manage',
            'ganeshwebui.model',
            'ganeshwebui.plugins.dashboard',
            'ganeshwebui.plugins.supervision',
            'ganeshwebui.plugins.supervision.model',
            'ganeshwebui.plugins.settings',
            'ganeshwebui.plugins.activity'],
    scripts = ['ganesh-web-client', 'ganeshwebui/plugins/supervision/metric-aggregator'],
    include_package_data=True,
    zip_safe=False,
    url = '',
    description = 'PostgreSQL Administration & Monitoring web client.',
    data_files = [('/usr/share/ganesh/', [
            'share/ganesh.conf.sample',
            'share/ssl/ganesh_CHANGEME.pem',
            'share/ssl/ganesh_CHANGEME.key',
            'share/ssl/ganesh_ca_certs_CHANGEME.pem',
            'share/sql/application.sql',
            'ganeshwebui/plugins/supervision/sql/supervision.sql']
    )]
)
