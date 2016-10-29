# Repository Setup

The `repository` is a PostgreSQL (>=9.5) database. It let temboard store its data, including users, agent registration and metrics data.

Usage of plugin `supervision` requires `tablefunc` extension. This extension is available as part of the extensions shipped with the source code of PostgreSQL, in the `contrib/` directory. Usually, the "contrib" package of PostgreSQL from your Linux distribution has it.

## Configuration

To ensure the browsing of the web interface is fast enough, please note the `work_mem` parameter PostgreSQL cluster hosting the repository should be set to at least `16MB`.

## Setup

To acces the `repository`, `temboard` needs to have its own user and database. To create them on a typical PostgreSQL setup, run the following commands:

```
sudo -u postgres createuser temboard -l -P
sudo -u postgres createdb -O temboard temboard
```

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

`temboard` SQL schema must be loaded. The schema is stored in the SQL files located in `/usr/share/temboard` after the installation:
```
psql -U temboard -1 -v'ON_ERROR_STOP=on' -f /usr/share/temboard/sql/application.sql temboard
```

If you plan to use the plugin `supervision`:
```
sudo -u postgres psql -U postgres -c "CREATE EXTENSION tablefunc" temboard
psql -U temboard -1 -v'ON_ERROR_STOP=on' -f /usr/share/temboard/supervision.sql temboard
```

## Configuration of temBoard

The last step is to configure temBoard to access the database. Edit `/etc/temboard/temboard.conf` and configure the parameters under the `[repository]`.

Then start the `temboard` service and check the log file (`/var/log/temboard/temboard.log` by default).

