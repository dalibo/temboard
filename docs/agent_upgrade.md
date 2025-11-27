<!--
RPM and DEB packages automatically restarts running services

If an upgrade requires manual steps:
stop service manually,
update the package,
execute manual steps
and restart the service manually.

-->

## From 9.0 to 10.0

You need to upgrade the temBoard Server **BEFORE** upgrading the temBoard Agents.

See [temBoard Server Upgrade](server_upgrade.md)

Here's the compatibility matrix:

|                      | temBoard Server v9              | temBoard Server v10          |
|----------------------|---------------------------------|-----------------------------|
| temBoard Agent v9    | Compatible                      | Compatible                  |
| temBoard Agent v10   | Not Supported                   | Compatible                  |

In other words:

* temboard Server v10 can manage temBoard Agents v9 and v10.
* temboard Server v9 cannot manage temBoard Agents v10

Once the temBoard Server has been upgraded to v10, you can upgrade the agents with the
classic commands:

=== "RHEL"

    ``` bash
    sudo yum install temboard-agent
    ```

=== "Debian / Ubuntu"

    ``` bash
    sudo apt update
    sudo apt install temboard-agent
    ```

Note: the former administation plugin is now obsolete you can remove the
`[administration]` section from the agent configuration file.

## From 8.2 to 9.0

You need to upgrade the temBoard Server **BEFORE** upgrading the temBoard Agents.

See [temBoard Server Upgrade](server_upgrade.md)

Here's the compatibility matrix:

|                      | temBoard Server v8              | temBoard Server v9          |
|----------------------|---------------------------------|-----------------------------|
| temBoard Agent v8    | Compatible                      | Use `temboard register`     |
| temBoard Agent v9    | Not Supported                   | Compatible                  |

In other words:

* temboard Server v9 can manage temBoard Agents v8 and v9.
* temboard Server v8 cannot manage temBoard Agents v9
* temboard Server v8 can manage temBoard Agents v8, however the temBoard Agent v8
  cannot register anymore to a temBoard v8 Server. Use `temboard register` instead.

Once the temBoard Server has been upgraded to v9, you can upgrade the agents with the
classic commands:

=== "RHEL"

    ``` bash
    sudo yum install temboard-agent
    ```

=== "Debian / Ubuntu"

    ``` bash
    sudo apt update
    sudo apt install temboard-agent
    ```


## From 8.1 to 8.2.1

Ensure [temBoard UI is upgraded](server_upgrade.md) first.

Install last the package:

=== "RHEL"

    ``` bash
    sudo yum install temboard-agent
    ```

=== "Debian"

    ``` bash
    sudo apt update
    sudo apt install temboard-agent
    ```


## From 8.0 to 8.1

Update the package:

=== "RHEL"

    ``` bash
    sudo yum install temboard-agent
    ```

=== "Debian"

    ``` bash
    sudo apt update
    sudo apt install temboard-agent
    ```


## From 7.11 to 8.0

temBoard Agent 8.0 requires temBoard UI 8.0.

Stop all agents:

``` bash
sudo systemctl stop temboard-agent@...
```

Update the package:

``` bash
sudo yum install temboard-agent
```

Repeat the following steps for each agents.

Edit configuration, comment out `key` parameter:

``` conf
[temboard]
# key = deadbeefc0ffee
```

Define `[temboard] ui_url` like this:

``` conf
[temboard]
ui_url = https://temboard.acme.tld:8888
```

Remove quotes around `pg_ctl` command like this:
``` conf
[administration]
#   Before:
# pg_ctl = '/usr/pgsql-15/bin/pg_ctl ...'
#   After:
pg_ctl = /usr/pgsql-15/bin/pg_ctl ...
```

!!! note

    Execute temboard-agent commands as `postgres` or another UNIX user as described by systemd unit.

    Execute temboard-agent commands with `--config` option for target argent.

Fetch signing key with the following command:

``` bash
temboard-agent --config=/etc/temboard-agent/.../temboard-agent.conf fetch-key
```

Flush background tasks with the following command:

``` bash
temboard-agent --config=/etc/temboard-agent/.../temboard-agent.conf tasks flush
```

Start the agent:

``` bash
sudo systemctl start temboard-agent@...
```

Check agent logs and dashboard in temBoard UI.

You can drop `users` file.


## Older versions

### 6.X to 7.0

First of all, beware that support for `RHEL/CentOS 6` has been dropped.

Stop the agent:

``` bash
sudo systemctl stop temboard-agent
```

Update the package:

``` bash
sudo yum install temboard-agent
```

Load the `pg_stat_statements` extension on the Postgres instance you are
monitoring with the agent. Please refer to the [official
documentation](https://www.postgresql.org/docs/current/pgstatstatements.html).

!!! Notes:

    -   You may need to install the PostgreSQL contrib package;
    -   You will need to restart the instance.

Enable the extension. Make sure you enable the extension on the database
set in the agent configuration.

``` SQL
CREATE EXTENSION pg_stat_statements;
```

Update configuration file `/etc/temboard-agent/temboard-agent.conf` to
add the `statements` plugin.

Start the agent:

``` bash
sudo systemctl start temboard-agent
```

### 5.X to 6.0

Stop the agent:

``` bash
sudo systemctl stop temboard-agent
```

Update the package:

``` bash
sudo yum install temboard-agent
```

Start the agent:

``` bash
sudo systemctl start temboard-agent
```

### 4.X to 5.0

Stop the agent:

``` bash
sudo systemctl stop temboard-agent
```

Update the package:

``` bash
sudo yum install temboard-agent
```

Start the agent:

``` bash
sudo systemctl start temboard-agent
```

### 3.X to 4.0

Stop the agent:

``` bash
sudo systemctl stop temboard-agent
```

Update the package:

``` bash
sudo yum install temboard-agent
```

Start the agent:

``` bash
sudo systemctl start temboard-agent
```

### 2.X to 3.0

Stop the agent:

``` bash
sudo systemctl stop temboard-agent
```

Update the package:

``` bash
sudo yum install temboard-agent
```

Load the maintenance plugin by adding \"maintenance\" in the list of
plugins in your temboard-agent.conf file.

Start the agent:

``` bash
sudo systemctl start temboard-agent
```

### 1.2 to 2.0

Stop the agent:

``` bash
sudo systemctl stop temboard-agent
```

Update the package:

``` bash
sudo yum install python-setuptools
sudo yum install temboard-agent
```

Start the agent:

``` bash
sudo systemctl start temboard-agent
```

### 1.1 to 1.2

Stop the agent:

``` bash
sudo systemctl stop temboard-agent
```

Update the package:

``` bash
sudo yum install temboard-agent
```

Start the agent:

``` bash
sudo systemctl start temboard-agent
```

### 0.0.1 to 1.1

Stop the agent:

``` bash
sudo systemctl stop temboard-agent
```

Update the package:

``` bash
sudo yum install temboard-agent
```

Update configuration file `/etc/temboard-agent/temboard-agent.conf`:

> -   `supervision` plugin name must be replaced by `monitoring`
> -   `settings` plugin name must be replaced by `pgconf`
> -   CA cert. file usage is not mandatory anymore, parameter
>     `ssl_ca_cert_file` can be commented

Start the agent:

``` bash
sudo systemctl start temboard-agent
```
