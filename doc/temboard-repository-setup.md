<h1>Repository Setup</h1>

The `repository` is a PostgreSQL (>=9.5) database. It lets temboard store data, users, agent registration and monitoring data.

## Configuration

To ensure browsing of the web interface is fast enough, please note `work_mem` parameter PostgreSQL cluster hosting the repository should be set to at least `16MB`.

## Authentication with password

The PostgreSQL user `temboard` must be allowed to connect to the repository database using password authentication (`md5`), please ensure the `pg_hba.conf` is configured accordingly. The password of `temboard` user should be set in the `temboard` configuration file, under section `[repository]`, parameter `password`.

For example, if the PostgreSQL cluster is on the same host as temboard, the following lines can be added to the `pg_hba.conf` file.

Insert the following lines before the first line that is not a comment:

```
local   temboard   temboard     md5
host    temboard   temboard   127.0.0.1/32   md5
host    temboard   temboard   ::1/128   md5
```

If the PostgreSQL cluster is on th different host, replace `127.0.0.1/32` by the IPv4 address (keeping `/32`) of the host of temboard and `::1` by its IPv6 address (keeping `/128`). Reload the configuration of the PostgreSQL cluster to activate the changes.

## Installation

To proceed with user and database creation, we're providing the script `create_repository.sh` located in `/usr/share/temboard`. This script must connects to the repository server with super-user privileges. By default, it tries to connect to local socket (`/var/run/postgresql`) and loads data structure into `temboard` database. Here is the list of environnement variables that can be used to change script's behaviour :
- `PGHOST` : repository host
- `PGUSER` : repository super-user
- `PGPASSWORD` : repository super-user's password
- `PGPORT` : repository listening TCP port
- `TEMBOARD_PASSWORD` : defines `temboard` user's password

Local usage:
```
sudo -u postgres /usr/share/temboard/create_repository.sh
```

Remote usage:
```
PGUSER=postgres PGHOST=repository.location PGPASSWORD=xxxxxxx /usr/share/temboard/create_repository.sh
```

## Configuration of temBoard

The last step is to configure temBoard to access the database. Edit `/etc/temboard/temboard.conf` and configure the parameters under the `[repository]`.

Then start the `temboard` service and check the log file (`/var/log/temboard/temboard.log` by default).
