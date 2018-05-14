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

AGENT_SSL_CERT = """-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAN2gVhFWzW9fMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMTUwOTI3MTYwMzU5WhcNMTgwNjIzMTYwMzU5WjBF
MQswCQYDVQQGEwJBVTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50
ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEAuqTeusBug8OzqixBD+T0H0F4FzNB66JARsVHR6iq4+Xuga/mYsVs6XRf
Jv0v6AxpVoSpbwdXavgpnCbJ+uPgZHythgPYBiaoLxs1iET6ftGHV0vefq393yMT
pecTEmK29UK1hgbapECxjRfcZi5eGBJfbbK3nkYqYpm2fn4Ezrgfe/j1i5vKLJPt
WbrMVMHV0ZFz5zcWbmwSdOgRcL/udGtithgYkJ1kntc02CjjgQxipTD71kbWH0m0
r3StTmJjMvAB6wCrwfne6Jr3l8LdlbjWj0FIOj48xCAklOpI1WLJMb7m2FRmg4Ap
4ASwO5Veh9NZmSPUtvy8w0pN26pcmwIDAQABo1AwTjAdBgNVHQ4EFgQUuKhW752w
EDArg21WsO+Toj4jVukwHwYDVR0jBBgwFoAUuKhW752wEDArg21WsO+Toj4jVukw
DAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAQEAtlssidslOMyLWMZqnI3C
lictMJBLjQyUtTMm5JKbnNnWiw8ZNuPmHfkuh8T70VYyVoJO+Ydvoa9N3F7tA1Yj
kie26BRIlPryHRVOhx6j3pSkr9CenIUURZogMJJ3ejCKcXDo5N5WGnjoIxaURc6u
Fso9fqFyZyOCDy1ZoVSXx1us67KYHIjhQThclPefwm411uKKEyjBNC2BhB3s1mQv
T10VuoXxjL8HsnnhRy1Z6WdIo6C+h9nzIhyrxiasdEo5alAnBRsKLES8sRvYYpQZ
loufCqV4IBnycPbvSlyg0PqIC+PL9hDTAa2LxrJojKm+KxRGJDaTPpMDvsxwBu0d
zg==
-----END CERTIFICATE-----
"""

AGENT_SSL_KEY = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC6pN66wG6Dw7Oq
LEEP5PQfQXgXM0HrokBGxUdHqKrj5e6Br+ZixWzpdF8m/S/oDGlWhKlvB1dq+Cmc
Jsn64+BkfK2GA9gGJqgvGzWIRPp+0YdXS95+rf3fIxOl5xMSYrb1QrWGBtqkQLGN
F9xmLl4YEl9tsreeRipimbZ+fgTOuB97+PWLm8osk+1ZusxUwdXRkXPnNxZubBJ0
6BFwv+50a2K2GBiQnWSe1zTYKOOBDGKlMPvWRtYfSbSvdK1OYmMy8AHrAKvB+d7o
mveXwt2VuNaPQUg6PjzEICSU6kjVYskxvubYVGaDgCngBLA7lV6H01mZI9S2/LzD
Sk3bqlybAgMBAAECggEBAIAtH2SjKIJG0MjKEXhn5JrebCmKove+emPfsV7t30YZ
Lt1TPmWQbYY5y+rLr62tcF3hRzaflRI6EOFS5hzth7mawdQqKZ23yIJpLi9CJ8EW
BdsWmFrpBFLMFP83HKrgrgLq6Bx98oMgho5913c42pevbme4d08zooIKTAC8bHLF
ZH5VespyfhjJ6ZIle5xzLzl0PPgVXHfcrcE+aeNucKGB8UeI2mbgJ0z+uoerflDi
ZOcW1qQM4O2ZHp8PGg7c7F4HP0z7ou+xzN+2/zSvjfWbp5YgdmltmNHe4U/JcjER
/54Ef64yNamXl1YmBw/k2FSOJYF0gMtcv80qJzaXlmkCgYEA7D8+gBCiIO01bLUJ
wlwa1Ei8oi7AThZD7T97uiwWxE50LRadyXVnC88nhF3T35guvyFeUU6IemIadgXq
Ue3ilEnz4LaoQFZevHeh7/fMC1CKPB3AcxQsVzCezUGsa7EWhXpCecuhxifH9hJh
3dWO05MQ0XMJmUD0FqWPYpy9oVUCgYEAyj/lj9g9ZX8BqS5wCa581kSVgmNdJ64C
vkMOb9ddKrenqffnGR98jBlitetEbGbcxn5QDdUBqLB10IkqeT06YRBKiuuf5rYt
XrD/aA+jWhfZ0RnD+IL7wIE7PETrrwVAb2xbtGEAEzefPPTtOywJcUFizt1HZjfz
qje5fqnKxi8CgYAVoeDmNx+xZicbMiSXoHlwcMydCSzguZc0tThuHrVi+lAXBNgj
51UtNqXGsBTDh5rYM4UAavGCS1Ni9T20jNTPgUoMjI0xfvcjyMySPZ14d8KAqLTD
lNhOj4wq/VV9cvS9+ij2IBhLHb9on9xIRNLUOsYyd5csak8vd69+dx3CFQKBgHBo
rSWS0ST9PyYR2lF3Ook4m0RaB6eLLpki2f5NW8nnQ3fTgg1Tk7ymS1fDCEebsC9e
ew4FCqQAV6rs4b96yVyzWkr2BOyM6pCLnZjvwCHNydFPGb2gx13KNescf0XKjHKh
biLGGu2TZ5zQoJ3XrvPUnJ9PG2TzyikcSavdoQcfAoGBALwbbYT7Z6Outz+R8ELd
LB7nMk7y8869Shi26siDtkN/gyzHyOrsAywK8LXq4TSqSt1YcBU60PlcqNFr4WpL
bt5GStClFArdcrLC3b4pmg519E4/jTfF2FjZ8zrFpfRlBNPZqHu0uKAHyEte+SBs
gEOuhwjYF4XZbnIZiNPGQSGZ
-----END PRIVATE KEY-----
"""
