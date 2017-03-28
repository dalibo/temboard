from setuptools import setup, find_packages

setup(
    name='temboard-agent',
    version='0.0.1',
    author='Dalibo',
    license='PostgreSQL',
    packages=find_packages(),
    scripts=[
        'temboard-agent', 'temboard-agent-password', 'temboard-agent-adduser'
    ],
    url='http://temboard.io/',
    description='Administration & monitoring PostgreSQL agent.',
    data_files=[('share/temboard-agent/', [
        'share/temboard-agent.conf.sample',
        'share/temboard-agent_CHANGEME.pem',
        'share/temboard-agent_CHANGEME.key',
        'share/temboard-agent_ca_certs_CHANGEME.pem',
        'share/temboard-agent.logrotate'
    ])])
