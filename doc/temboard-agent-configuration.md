<h1>Agent configuration</h1>

## Key & Hostname

In the `temboard-agent.conf` file, 2 important parameters must be configured to make the agent interact with the central server:

* The `hostname` is used to identify the Agent. It must be a **unique** and
  [fully qualified domain name](https://en.wikipedia.org/wiki/Fully_qualified_domain_name) ( e.g. ``db1.mydomain.foo`` ).
  Note that ``localhost`` is not a valid value for this parameter.

* The `key` is used to authentify the Agent. It must be a long series of characters and you must keep it secret. The best
  way to configure the agent key is to generate a random string of letters and number:

```
cat /dev/urandom | tr -dc '[:alnum:]' | fold -w 64 | head -1
```


## SSL certificate

`temboard-agent` embeds a lightweight HTTPS server aimed to serve its API, thus it is required to use a SSL certificate. As long as the agent's API is not reachable through a public interface, usage of self-signed certificates is safe.

### Using provided SSL certificate
`temboard-agent` provides a ready to use self-signed SSL certifcate located in `/usr/share/temboard-agent` directory, if you don't want to use it, you can create a new one with the `openssl` binary.
```
sudo cp /usr/share/temboard-agent/temboard-agent_CHANGEME.key /etc/temboard-agent/ssl/.
sudo cp /usr/share/temboard-agent/temboard-agent_CHANGEME.pem /etc/temboard-agent/ssl/.
sudo chown postgres.postgres /etc/temboard-agent/ssl/*
```

### Build a new self-signed certificate

To build a new SSL certifcate:
```
sudo -u postgres openssl req -new -x509 -days 365 -nodes -out /etc/temboard-agent/ssl/localhost.pem -keyout /etc/temboard-agent/ssl/localhost.key
```

Then, `ssl_cert_file` and `ssl_key_file` parameters from `temboard-agent.conf` file need to be set respectively to `/etc/temboard-agent/ssl/localhost.pem` and `/etc/temboard-agent/ssl/localhost.key`.

### CA certificate file

The plugin `supervision` sends periodically collected data to the collector (API served by the temBoard UI web server) through HTTPS. To allow this data flow, the HTTPS client implemented by the agent needs to have the UI's SSL certifcate (.pem) stored in its CA certificate file. temBoard agent embeds a default CA cert. file containing default temBoard UI SSL certificate.
```
sudo cp /usr/share/temboard-agent/temboard-agent_ca_certs_CHANGEME.pem /etc/temboard-agent/ssl/ca_certs_localhost.pem
```

`ssl_ca_cert_file` parameter in section `[supervision]` from the configuration file needs to be set to `/etc/temboard-agent/ssl/ca_certs_localhost.pem`.

### Restrictions on SSL files
```
sudo chmod 0600 /etc/temboard-agent/ssl/*
```

### Access to PostgreSQL Cluster

The agent needs a PostgreSQL superuser. By default, it is configured to work with `postgres` user.

To create a dedicated one with password authentication:
```
sudo -u postgres createuser temboard -s -P
```

This superuser should be able to connect to the cluster through the unix socket using a password, check `pg_hba.conf` file and reload configuration.
Example of `pg_hba.conf` entry:
```
local   postgres        temboard                                  md5
```

The access to the PostgreSQL cluster is then configured in the `[postgresql]` section of the `/etc/temboard-agent/temboard-agent.conf` file.

### Users

When interacting with the agent using HTTP, for example when accessing certain pages in the Web UI, an authentication is required. Accounts are created using the `temboard-agent-adduser`.

Add a first user:
```
sudo -u postgres temboard-agent-adduser
```

### Registration in the Web UI of the supersivion plugin

If you want to use the supervision plugin, you need to setup the `collector_url`. It lets the agent know where to post its data.
Just change the hostname to point to the server. Since the Server is only reachable using HTTPS, the UI SSL certificate
(or CA certificates that has issued it) must be in the filepath where `ssl_ca_cert_file` points.


## The configuration file

The configuration file `temboard-agent.conf` is formated using INI format. Configuration parameters are distributed under sections:
- `[temboard]`: this is the main section grouping core parameters;
- `[postgresql]`: parameters related to the PostgreSQL cluster that the agent is connected to;
- `[logging]`: how and where to log;
- `[dashboard]`: parameters of the plugin `dashboard`;
- `[supervision]`: plugin `supervision`;
- `[administration]`: plugin `administration`.

### `[temboard]`
  - `port`: port number that the agent will listen on to serve its `HTTP API`. Default: `2345`;
  - `address`: IP v4 address that the agent will listen on. Default: `0.0.0.0` (all);
  - `users`: Path to the file containing the list of the users allowed to use the `HTTP API`. Default: `/etc/temboard-agent/users`;
  - `plugins`: Array of plugin (name) to load. Default: `["supervision", "dashboard", "settings", "administration", "activity"]`;
  - `ssl_cert_file`: Path to SSL certificate file (.pem) for the embeded HTTPS process serving the API. Default: `/etc/temboard-agent/ssl/temboard-agent_CHANGEME.pem`;
  - `ssl_key_file`: Path to SSL private key file. Default: `/etc/temboard-agent/ssl/temboard-agent_CHANGEME.key`;
  - `home`: Path to agent home directory, it contains files used to store temporary data. When running multiple agents on the same host, each agent must have its own home directory. Default: `/var/lib/temboard-agent/main`.
  - `hostname`: Overrides real machine hostname. Must be a valid FQDN. Default: `None`;

### `[postgresql]`
  - `host`: Path to PostgreSQL unix socket. Default: `/var/run/postgresql`;
  - `port`: PostgreSQL port number. Default: `5432`;
  - `user`: PostgreSQL user, Must be a super-user. Default: `postgres`;
  - `password`: User password. Default: `None`;
  - `dbname`: Database name for the connection. Default: `postgres`;
  - `instance`: Cluster name. Default: `main`.
  - `key`: Authentication key used to send data to the UI. Default: `None`;

### `[logging]`
  - `method`: Method used to send the logs: `stderr`, `syslog` or `file`. Default: `syslog`;
  - `facility`: Syslog facility. Default: `local0`;
  - `destination`: Path to the log file. Default: `/dev/log`;
  - `level`: Log level, can be set to `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`. Default: `INFO`.

### `[dashboard]`
  - `scheduler_interval`: Time interval, in second, between each run of the process collecting data used to render the dashboard. Default: `2`;
  - `history_length`: Number of record to keep. Default: `20`.

### `[supervision]`
  - `dbnames`: Database name list (comma separator) to supervise. * for all. Default: `*`;
  - `collector_url`: Collector URL. Default: `None`;
  - `probes`: List of probes to run, comma separator, * for all. Default: `*`;
  - `scheduler_interval`: Interval, in second, between each run of the process executing the probes. Default: `60`;
  - `ssl_ca_cert_file `: File where to store collector's SSL certificate. Default: `None`.

### `[administration]`
  - `pg_ctl`: External command used to start/stop PostgreSQL. Default: `None`.
