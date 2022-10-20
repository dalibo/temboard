<h1>Configure the server</h1>

The configuration file `temboard.conf` is formated using INI format.

Configuration parameters are distributed under sections:


## `temboard`

This is the main section grouping core parameters :


  - **port**
  Port number that `temboard` will listen on.
  Default: `8888`

  - **address**
  IP v4 address that `temboard` will listen on.
  Default: `0.0.0.0`

  - **ssl_cert_file**
  Path to SSL certificate file (.pem).
  Default: *empty*

  - **ssl_key_file**
  Path to SSL private key file.
  Default: *empty*

  - **ssl_ca_cert_file**
  File where to store each agent's SSL certificate. Comment it to disable SSL
  certifcate checks.
  Default: *empty*

  - **cookie_secret**
  Secret key used to crypt cookie content.
  Default: *empty*;

  - **plugins**
  Array of plugin name to load.
  Default: `["monitoring", "dashboard", "pgconf", "activity", "maintenance",
  "statements"]`


## `repository`

Connection parameters to the data repository aka `temboard` database.


  - **host**
  Repository host name or address.
  Default: `/var/run/postgresql`

  - **port**
  Repository port number.
  Default: `5432`

  - **user**
  Connection user.
  Default: `temboard`

  - **password**
  User password.
  Default: `temboard`

  - **dbname**
  Database name.
  Default: `temboard`


## `logging`

How and where to log.


  - **method**
  Method used to send the logs: `stderr`, `syslog` or `file`.
  Default: `stderr`

  - **facility**
  Syslog facility.
  Default: `local0`

  - **destination**
  Log file path.
  Default: `/dev/log`

  - **level**
  Log level, can be set to `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`.
  Default: `INFO`


## `notifications`

This section groups SMTP and Twilio parameters to send notifications.


  - **smtp_host**
  SMTP host.
  Default: *empty*

  - **smtp_port**
  SMTP port.
  Default: *empty*

  - **smtp_tls**
  Enable TLS connexion.
  Default: False

  - **smtp_login**
  SMTP login.
  Default: *empty*

  - **smtp_password**
  SMTP password.
  Default: *empty*

  - **smtp_from_addr**
  SMTP from address.
  Default: *empty*

  - **twilio_account_sid**
  Twillio account SID.
  Default: *empty*

  - **twilio_auth_token**
  Twilio authentication token.
  Default: *empty*

  - **twilio_from**
  Twilio from phone number
  Default: *empty*


## `monitoring`

Parameters related to the monitoring plugin.


  - **purge_after**
  Set the amount of data to keep, expressed in days.
  Default: 730


## `statements`

Parameters related to the statements plugin.


  - **purge_after**
  Set the amount of data to keep, expressed in days.
  Default: 7
