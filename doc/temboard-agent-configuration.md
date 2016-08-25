# `temboard-agent` configuration

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

### `[postgresql]`
  - `host`: Path to PostgreSQL unix socket. Default: `/var/run/postgresql`;
  - `port`: PostgreSQL port number. Default: `5432`;
  - `user`: PostgreSQL user, Must be a super-user. Default: `postgres`;
  - `password`: User password. Default: `None`;
  - `dbname`: Database name for the connection. Default: `postgres`;
  - `instance`: Cluster name. Default: `main`.

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
