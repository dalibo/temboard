# coding: utf-8

import os.path

WORK_PATH = '/tmp'

# Debian / 9.5
# PG_BIN = '/usr/lib/postgresql/9.5/bin'
# Gentoo / 9.5
PG_BIN = '/usr/lib64/postgresql-9.5/bin'
PG_PORT = 5445
PG_USER = 'temboard'
PG_PASSWORD = 'temboard'
PG_SETTINGS = [
    "log_min_duration_statement = 0\n",
    "log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '\n"
]

AGENT_HOST = "127.0.0.1"
AGENT_PORT = 12446
AGENT_USER = 'temboard'
AGENT_PASSWORD = 'password'

AGENT_CONFIG = """
[temboard]
# HTTP port
port = %(temboard_port)s
# Bind address
address = 127.0.0.1
# user & password file
users = %(temboard_users)s
# SSL: private key file path (.key)
ssl_key_file = %(temboard_ssl_key_file)s
# SSL: certificat file path (.pem)
ssl_cert_file = %(temboard_ssl_cert_file)s
home = %(temboard_home)s
hostname = test.temboard.io

[postgresql]
host = %(postgresql_host)s
port = %(postgresql_port)s
user = %(postgresql_user)s
password = %(postgresql_password)s
dbname = postgres

[logging]
# syslog or file
method=file
destination = %(logging_destination)s
level = DEBUG

[administration]
pg_ctl = '/usr/bin/sudo /etc/init.d/postgresql %%s 9.5'

# üniçode comment.
"""  # noqa

AGENT_CONFIG_PLUGINS = """\
[temboard]
plugins = %(temboard_plugins)s
"""

AGENT_CONFIG_MONITORING = """\
[monitoring]
dbnames = '*'
# agent_key = ''
collector_url = http://localhost:8888/collector/
# probes = ''
# interval = 60
ssl_ca_cert_file = %(monitoring_ssl_ca_cert_file)s
"""

sharedir = os.path.join(os.path.dirname(__file__), '../../../share')
AGENT_SSL_CERT = open(sharedir + '/temboard-agent_CHANGEME.pem').read()
AGENT_SSL_KEY = open(sharedir + '/temboard-agent_CHANGEME.key').read()
