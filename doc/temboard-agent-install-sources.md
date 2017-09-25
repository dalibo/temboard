<h1>Agent installation from PyPI</h1>

## Dependencies

  - `python` &ge; **2.7**
  - `python-setuptools` &ge; **0.6**

## Installation

```
sudo pip install temboard-agent
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
