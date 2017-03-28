# temBoard agent installation from sources and configuration

## Dependencies

  - `python` &ge; **2.7**
  - `python-setuptools` &ge; **0.6**

## Installation

To install Python `setuptools` with `pip`:
```
sudo pip install setuptools
```

Proceed with the installation of the agent:
```
cd temboard/temboard-agent/
sudo cp -r share/ /usr/share/temboard-agent
sudo python setup.py install
```


## Prepare directories and files

Creation of directories for configuration and SSL files:
```
sudo mkdir /etc/temboard-agent
sudo mkdir /etc/temboard-agent/ssl
```

Home directory:
```
sudo mkdir /var/lib/temboard-agent
sudo mkdir /var/lib/temboard-agent/main
```

Logging directory:
```
sudo mkdir /var/log/temboard-agent
```

Copy the sample configuration file:
```
sudo cp /usr/share/temboard-agent/temboard-agent.conf.sample /etc/temboard-agent/temboard-agent.conf
```

Copy the logrotate configuration file:
```
sudo cp /usr/share/temboard-agent/temboard-agent.logrotate /etc/logrotate.d/temboard-agent
```

Change owner and rights:
```
sudo chown -R postgres.postgres /var/lib/temboard-agent
sudo chown postgres.postgres /var/log/temboard-agent
sudo chown -R postgres.postgres /etc/temboard-agent
sudo chmod 0600 /etc/temboard-agent/temboard-agent.conf
```


## Configuration

Before starting the agent, see `doc/temboard-agent-configuration.md` for post-installation tasks.

## Operating the agent

### Start
```
sudo -u postgres temboard-agent -d -p /var/lib/temboard-agent/main/temboard-agent.pid
```

### Stop
```
sudo kill $(cat /var/lib/temboard-agent/main/temboard-agent.pid)
```

### Reload configuration
```
sudo kill -HUP $(cat /var/lib/temboard-agent/main/temboard-agent.pid)
```

## Smoke test

Start the agent, then try:
```
curl -k https://127.0.0.1:2345/discover
curl -k -X POST -H "Content-Type: application/json" -d '{"username": "<username>", "password": "<password>"}' https://127.0.0.1:2345/login
```

## Functional tests

```
sudo apt-get install python-rednose python-nose
cd temboard-agent/test
cp test/configuration.py.sample test/configuration.py
nosetests --rednose -v test_*
```
