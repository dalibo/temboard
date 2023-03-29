<h1>Configure the agent</h1>

temBoard agent reads configuration from arguments, environment and file.
Defaut configuration file is `/etc/temboard-agent/temboard-agent.conf`.
You can change this with `TEMBOARD_CONFIGFILE` envvar or `--configfile`
switch.

temBoard agent always searches for a directory whose name is built with
the config file and the `.d` suffix. Thus the default config directory
is `/etc/temboard-agent/temboard-agent.conf.d`. temBoard agent reads
only files suffixed with `.conf`. temBoard agent reads files in POSIX
sort order: uppercase precedes lowercase.

The configuration file is mandatory. The configuration directory is
optional.

The configuration file is in [INI-style
format](https://docs.python.org/3/library/configparser.html#supported-ini-file-structure)
as implemented by Python stlib config parser. Configuration parameters
are distributed under sections:

- `temboard`: this is the main section grouping core parameters;
- `postgresql`: parameters related to the PostgreSQL cluster that
  the agent is connected to;
- `logging`: how and where to log;
- `dashboard`: parameters of the plugin `dashboard`;
- `monitoring`: plugin `monitoring`;
- `administration`: plugin `administration`,
- `maintenance`: plugin `maintenance`.
- `statements`: plugin `statements`;


# `temboard`

- `ui_url`: base URL of the UI managing this agent.
- `port`: port number that the agent will listen on to serve its
  `HTTP API`. Default: `2345`;
- `address`: IP v4 address that the agent will listen on. Default:
  `0.0.0.0` (all);
- `plugins`: Array of plugin (name) to load. Default:
  `["monitoring", "dashboard", "pgconf", "administration", "activity", "maintenance", "statements"]`;
- `ssl_cert_file`: Path to SSL certificate file (.pem) for the
  embeded HTTPS process serving the API. Default:
  `/etc/temboard-agent/temboard-agent_CHANGEME.pem`;
- `ssl_key_file`: Path to SSL private key file. Default:
  `/etc/temboard-agent/temboard-agent_CHANGEME.key`;
- `home`: Path to agent home directory, it contains files used to
  store temporary data. When running multiple agents on the same
  host, each agent must have its own home directory. Default:
  `/var/lib/temboard-agent/main`.
- `hostname`: Overrides real machine FQDN. Must be unique for each agent.
  Default: `None`;


# `postgresql`

- `host`: Path to PostgreSQL unix socket. As of now, temboard-agent
  requires superuser access using local UNIX socket only. Default:
  `/var/run/postgresql`;
- `port`: PostgreSQL port number. Default: `5432`;
- `user`: PostgreSQL user. Must be a super-user. Default:
  `postgres`;
- `password`: User password. Default: `None`;
- `dbname`: Database name for the connection. Default: `postgres`;
- `instance`: Cluster name. Default: `main`.
- `key`: Authentication key used to send data to the UI. Default:
  `None`;


# `logging`

- `method`: Method used to send the logs: `stderr`, `syslog` or
  `file`. Default: `stderr`;
- `facility`: Syslog facility. Default: `local0`;
- `destination`: Path to the log file. Default: `/dev/log`;
- `level`: Log level, can be set to `DEBUG`, `INFO`, `WARNING`,
  `ERROR` or `CRITICAL`. Default: `INFO`.
- `debug`: A comma separated list of loggers to which level will be
  set to `DEBUG`.


# `dashboard`

- `scheduler_interval`: Time interval, in second, between each run
  of the process collecting data used to render the dashboard.
  Default: `2`;
- `history_length`: Number of record to keep. Default: `150`.


# `monitoring`

- `dbnames`: Database name list (comma separated) to supervise. \*
  for all. Default: `*`;
- `probes`: List of probes to run (comma separated). \* for all.
  Default: `*`;
- `scheduler_interval`: Interval, in second, between each run of the
  process executing the probes. Default: `60`;


# `administration`

- `pg_ctl`: External command used to start/stop PostgreSQL. Default:
  `None`.


# `statements`

- `dbname`: Name of the database hosting `pg_stat_statements` view,
  enabled through creation of the eponymous extension. Default:
  `postgres`.
