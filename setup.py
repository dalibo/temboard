from setuptools import setup, find_packages

setup(
    name='temboard-agent',
    version='1.1',
    author='Dalibo',
    author_email='contact@dalibo.com',
    license='PostgreSQL',
    url='http://temboard.io/',
    description='Administration & monitoring PostgreSQL agent.',
    long_description=open('README.rst').read(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 2 :: Only",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: System :: Monitoring",
    ],
    packages=find_packages(),
    scripts=[
        'temboard-agent',
        'temboard-agent-adduser',
        'temboard-agent-password',
        'temboard-agent-register',
    ],
    data_files=[
        ('share/temboard-agent/quickstart/', [
            'share/temboard-agent.conf',
            'share/temboard-agent_CHANGEME.pem',
            'share/temboard-agent_CHANGEME.key',
            'share/temboard-agent_ca_certs_CHANGEME.pem',
            'share/temboard-agent.logrotate',
            'share/users',
        ]),
        ('/usr/share/temboard-agent/', [
            'share/temboard-agent.conf',
            'share/temboard-agent.logrotate',
        ]),
        ('lib/systemd/system', ['packaging/temboard-agent.service']),
    ])
