from setuptools import setup

requires = [
]

setup(
    name = 'temboard-agent',
    version = '0.0.1',
    author = 'Dalibo',
    license = 'PostgreSQL',
    packages = [
                'temboardagent',
                'temboardagent.plugins.supervision',
                'temboardagent.plugins.dashboard',
                'temboardagent.plugins.administration',
                'temboardagent.plugins.settings',
                'temboard.plugins.activity'],
    scripts = [
                'temboard-agent',
                'temboard-agent-password',
                'temboard-agent-adduser'],
    url = '',
    description = 'Administration & monitoring PostgreSQL agent.',
    data_files = [('/usr/share/temboard-agent/', [
                                            'share/temboard-agent.conf.sample',
                                            'share/temboard-agent_CHANGEME.pem',
                                            'share/temboard-agent_CHANGEME.key',
                                            'share/temboard-agent_ca_certs_CHANGEME.pem'])]
)
