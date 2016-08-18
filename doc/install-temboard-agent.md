# Temboard agent installation from sources and configuration

## Dependencies

  - `python` &ge; **2.7**
  - `python-setuptools` &ge; **0.6**

## Installation

To install Python `setuptools` with `pip`:
```
$ sudo pip install setuptools
```

Proceed with the installation of the agent:
```
$ cd temboard/temboard-agent/
$ sudo python setup.py install
```


## Prepare directories and files

Creation of directories for configuration and SSL files:
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

Change owner and rights:
```
$ sudo chown -R postgres.postgres /var/lib/temboard-agent
$ sudo chown postgres.postgres /var/log/temboard-agent
$ sudo chown -R postgres.postgres /etc/temboard-agent
$ sudo chmod 0600 /etc/temboard-agent/temboard-agent.conf
```


## SSL certificate

`temboard-agent` embeds a lightweight HTTPS server aimed to serve its API, thus it is required to use a SSL certificate. As long as the agent's API is not reachable through a public interface, usage of self-signed certificates is safe.

### Using provided SSL certificate
`temboard-agent` provides a ready to use self-signed SSL certifcate located in `/usr/share/temboard-agent` directory, if you don't want to use it, you can create a new one with the `openssl` binary.
```
$ sudo cp /usr/share/temboard-agent/temboard-agent_CHANGEME.key /etc/temboard-agent/ssl/.
$ sudo cp /usr/share/temboard-agent/temboard-agent_CHANGEME.pem /etc/temboard-agent/ssl/.
$ sudo chown postgres.postgres /var/log/temboard-agent/ssl/*
```

### Build a new self-signed certificate

To build a new SSL certifcate:
```
$ sudo -u postgres openssl req -new -x509 -days 365 -nodes -out /etc/temboard-agent/ssl/localhost.pem -keyout /etc/temboard-agent/ssl/localhost.key
```

Then, `ssl_cert_file` and `ssl_key_file` parameters from `temboard-agent.conf` file need to be set respectively to `/etc/temboard-agent/ssl/localhost.pem` and `/etc/temboard-agent/ssl/localhost.key`.

### CA certificate file

The plugin `supervision` sends periodically collected data to the collector (an API served by the temboard UI web server) through HTTPS. To allow this data flow, the HTTPS client implemented by the agent needs to have the UI's SSL certifcate (.pem) stored in its CA certificate file. Temboard agent embeds a default CA cert. file containing default Temboard UI SSL certificate.
```
$ sudo cp /usr/share/temboard-agent/temboard-agent_ca_certs_CHANGEME.pem /etc/temboard-agent/ssl/ca_certs_localhost.pem
```

`ssl_ca_cert_file` parameter in section `[supervision]` from the configuration file needs to be set to `/etc/temboard-agent/ssl/ca_certs_localhost.pem`.

### Restrictions on SSL files
```
$ sudo chmod 0600 /etc/temboard-agent/ssl/*
```


## The configuration file

The configuration file `temboard-agent.conf` is formated using INI format. Configuration parameters are distributed under sections:
  - `[temboard]`: this is the main section grouping core parameters;
  - `[postgresql]`: parameters related to the PostgreSQL instance that the agent is connected to;
  - `[logging]`: how and where to log;
  - `[dashboard]`: parameters of the plugin `dashboard`;
  - `[supervision]`: plugin `supervision`;
  - `[administration]`: plugin `administration`.

### `[temboard]`
  - `port`: port number that the agent will listen on to serve its `HTTP API`. Default: `2345`;
  - `address`: IP address that the agent will listen on. Default: `0.0.0.0` (all);
  - `users`: Path to the file containing the list of the users allowed to use the `HTTP API`. Default: `/etc/temboard-agent/users`;
  - `plugins`: Array of plugin (name) to load. Default: `["supervision", "dashboard", "settings", "administration", "activity"]` (None);
  - `ssl_cert_file`: Path to SSL certificate file (.pem) for the embeded HTTPS process serving the API. Default: `/etc/temboard-agent/ssl/temboard-agent_CHANGEME.pem`;
  - `ssl_key_file`: Path to SSL private key file. Default: `/etc/temboard-agent/ssl/temboard-agent_CHANGEME.key`;
  - `home`: Path to agent home directory, it contains files used to store temporary data. When running multiple agents on the same host, each agent must have its own home directory. Default: `/var/lib/temboard-agent/main`.

### `[postgresql]`
  - `host`: Path to PostgreSQL unix socket. Default: `/var/run/postgresql`;
  - `port`: PostgreSQL port number. Default: `5432`;
  - `user`: PostgreSQL user, Must be a super-user. Default: `postgres`;
  - `password`: User password. Default: `None`;
  - `dbname`: Database name for the connection. Default: `postgres`;
  - `instance`: Instance name. Default: `main`.

### `[logging]`
  - `method`: Method used to send the logs: `syslog` or `file`. Default: `syslog`;
  - `facility`: Syslog facility. Default: `local0`;
  - `destination`: Path to the log file. Default: `/dev/log`;
  - `level`: Log level, can be set to `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`. Default: `INFO`.

### `[dashboard]`
  - `scheduler_interval`: Time interval, in second, between each run of the process collecting data used to render the dashboard. Default: `2`;
  - `history_length`: Number of record to keep. Default: `20`.

### `[supervision]`
  - `hostname`: Overide real machine hostname. Default: `None`;
  - `dbnames`: Database name list (comma separator) to supervise. * for all. Default: `*`;
  - `agent_key`: Authentication key used to send data to the collector (API /supervision/collector of the UI). Default: `None`;
  - `collector_url`: Collector URL. Default: `None`;
  - `probes`: List of probes to run, comma separator, * for all. Default: `*`;
  - `scheduler_interval`: Interval, in second, between each run of the process executing the probes. Default: `60`;
  - `ssl_ca_cert_file `: File where to store collector's SSL certificate. Default: `None`.

### `[administration]`
  - `pg_ctl`: External command used to start/stop PostgreSQL. Default: `None`.


## PostgreSQL

The agent needs a PostgreSQL superuser.

To create a dedicated one with password authentication:
```
$ sudo -u postgres createuser temboard -s -P
```

This superuser should be able to connect to the instance through the unix socket using a password, check `pg_hba.conf` file and reload configuration.
Example of `pg_hba.conf` entry:
```
local   postgres        temboard                                  md5
```    

## Users

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

## Functional tests

```
$ sudo apt-get install python-rednose python-nose
$ cd temboard-agent/test
$ nosetests --rednose -v test_*
```
