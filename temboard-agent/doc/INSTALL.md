# Temboard agent installation from sources

## Dependencies

  - `python` &ge; **2.7**
  - `python-setuptools` &ge; **0.6**


## Installation

To install Python `setuptools` with `pip`:
```
$ sudo pip install setuptools
```

Proceed with the agent installation:
```
$ cd temboard-agent/
$ sudo python setup.py install
```

## Prepare directories and files

Creation of directories for the agent configuration file and SSL files:
```
$ sudo mkdir /etc/temboard-agent
$ sudo mkdir /etc/temboard-agent/ssl
```

Home directory:
```
$ sudo mkdir /var/lib/temboard-agent
$ sudo mkdir /var/lib/temboard-agent/main
```

Logging directory:
```
$ sudo mkdir /var/log/temboard-agent
```

Copy the sample configuration file:
```
$ sudo cp /usr/share/temboard-agent/temboard-agent.conf.sample /etc/temboard-agent/temboard-agent.conf
```

Copy dummies self-signed SSL key and cacerts files:
```
$ sudo cp /usr/share/temboard-agent/temboard-agent_* /etc/temboard-agent/ssl/.
```

Change owner and rights:
```
$ sudo chown -R postgres.postgres /var/lib/temboard-agent
$ sudo chown postgres.postgres /var/log/temboard-agent
$ sudo chown -R postgres.postgres /etc/temboard-agent
$ sudo chmod 0600 /etc/temboard-agent/ssl/*
```

## PostgreSQL

The agent needs a PostgreSQL superuser.

To create a dedicated one with password authentication:
```
$ sudo -u postgres createuser temboard-agent -s -P
```

This superuser should be able to connect to the instance through the unix socket using a password, check `pg_hba.conf` file and reload configuration.
Example of `pg_hba.conf` entry:
```
local   postgres        temboard-agent                                  md5
```    


## Configuration

Edit and adapt the configuration file `/etc/temboard-agent/temboard-agent.conf`, especialy sections: `postgresql` and `supervision`.

Add a first user:
```
$ sudo -u postgres temboard-agent-adduser
```

## Exploiting the agent

### Start
```
$ sudo -u postgres temboard-agent -d -p /var/lib/temboard-agent/main/temboard-agent.pid
```

### Stop
```
$ sudo kill $(cat /var/lib/temboard-agent/main/temboard-agent.pid)
```

### Reload configuration
```
$ sudo kill -HUP $(cat /var/lib/temboard-agent/main/temboard-agent.pid)
```

## Smoke test

Start the agent, then try:
```
$ curl -k https://127.0.0.1:2345/discover
$ curl -k -X POST -H "Content-Type: application/json" -d '{"username": "<username>", "password": "<password>"}' https://127.0.0.1:2345/login
```
