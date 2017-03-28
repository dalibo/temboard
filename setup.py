from setuptools import setup, find_packages
import subprocess


try:
    # Release mode
    VERSION = (
        subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"])
        .strip().decode()
    )
except subprocess.CalledProcessError:
    # pip install mode
    with open('PKG-INFO') as fo:
        for line in fo:
            if not line.startswith('Version: '):
                continue
            VERSION = line.replace('Version: ', '').strip()
            break

setup(
    name='temboard-agent',
    version=VERSION,
    author='Dalibo',
    license='PostgreSQL',
    packages=find_packages(),
    scripts=[
        'temboard-agent',
        'temboard-agent-adduser',
        'temboard-agent-password',
        'temboard-agent-register',
    ],
    url='http://temboard.io/',
    description='Administration & monitoring PostgreSQL agent.',
    long_description=open('README.rst').read(),
    data_files=[
        ('share/temboard-agent/', [
            'share/temboard-agent.conf.sample',
            'share/temboard-agent_CHANGEME.pem',
            'share/temboard-agent_CHANGEME.key',
            'share/temboard-agent_ca_certs_CHANGEME.pem',
            'share/temboard-agent.logrotate'
        ]),
        ('lib/systemd/system', ['temboard-agent.service']),
    ])
