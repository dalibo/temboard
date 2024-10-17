[preferred installation method]: server_install.md#install
[upgrade the agents]: agent_upgrade.md

<!--
RPM and DEB packages automatically restarts running services

If an upgrade requires manual steps:
stop service manually,
update the package,
execute manual steps
and restart the service manually.

-->

## From 8.2 to 9.0

Temboard 9 introduces a major change: The concepts of `user groups` and
`instance groups` are replace by a single concept of `environments`

* An environment can have several members (users)
* An environment can have several instances
* An instance belongs to only one environment

To upgrade a Temboard 8 server, you must use the `temboard migratedb upgrade` command.

Stop temBoard service:

``` bash
sudo systemctl stop temboard
```

Update the package:

=== "RHEL"

    ``` bash
    sudo yum install temboard
    ```

=== "Debian"

    ``` bash
    sudo apt update
    sudo apt install temboard
    ```

Upgrade the database schema:

``` bash
sudo -u temboard temboard migratedb upgrade
```

Start temBoard service:

``` bash
sudo systemctl start temboard
```


## From 8.1 to 8.2.1

=== "RHEL"

    Stop the service.

    ``` bash
    sudo systemctl stop temboard
    ```

    Remove the old package:

    ``` bash
    sudo rpm --noscripts --erase temboard
    ```

    Install last package:

    ``` bash
    sudo yum install temboard-8.2.1
    ```

    Enable the service:

    ``` bash
    sudo systemctl start temboard
    ```

=== "Debian"

    ``` bash
    sudo apt update
    sudo apt install temboard
    ```


## From 8.0 to 8.1

Update the package:

=== "RHEL"

    ``` bash
    sudo yum install temboard
    ```

=== "Debian"

    ``` bash
    sudo apt update
    sudo apt install temboard
    ```


## Upgrade `7.11` to `8.0`

temBoard UI 8.0 supports agent version 7.11 and 8.0.
Upgrade temBoard UI before upgrading agents.

temBoard 8.0 requires changes in database schema.

**Stop service**

Stop `temboard` service:

``` shell
sudo systemctl stop temboard
```

**Update package**

Update temboard package with your [preferred installation method].

**Upgrade Database Schema**

Then apply `repository` database upgrade with the following command:

``` shell
sudo -u temboard temboard migratedb upgrade
```

**Flush tasks**

Flush background tasks with the following command:

``` shell
sudo -u temboard temboard tasks flush
```

**Generate Signing Key**

Generate signing key:

``` console
sudo -u temboard temboard generate-key
```

**Start service**

Start `temboard` service:

```shell
sudo systemctl start temboard
```


## Older versions

### Upgrade `7.X` to `7.9`

**Stop service**

Stop `temboard` service:

``` shell
sudo systemctl stop temboard
```

**Update package**

Update temboard package with your [preferred installation method].

**Upgrade SQL procedures**

Then apply `repository` database upgrade with the following command:

``` shell
sudo -u temboard temboard-migratedb upgrade
```

**Start service**

Start `temboard` service:

```shell
sudo systemctl start temboard
```

!!! note

    Upon restart, temBoard UI will fetch missing monitoring supervision.
    This may take some time and ressources depending on the time of interruption and the number of monitoring instances.


### Upgrade `6.X` to `7.0`

**Update agents**

temBoard UI 7.0 is compatible with agent 6.X. Still, we suggest you to [upgrade
the agents](agent_upgrade.md).

*Note: An upgrade of the agent is required if you want to use the new `statements`
plugin.*

**Stop service**

Stop `temboard` service:

``` shell
sudo systemctl stop temboard
```

**Update package**

Update temboard package with your [preferred installation method]

**Upgrade database structure**

With the addition of the `statements` plugin, an upgrade of the repository
database schema is required.

First of all, please make sure that you first did the **upgrade from 5 to 6**.
This is very important!

Then apply `repository` database structure upgrade with the following command:

``` shell
sudo -u temboard temboard-migratedb upgrade
```

**Start service**

Start `temboard` service:

```shell
sudo systemctl start temboard
```

**Activate statements plugin**

Open temBoard in your browser and activate the `statements` plugin for the
different instances on which you want to use it.

---

### Upgrade `5.X` to `6.0`

temBoard UI 6.0 is compatible with agent 5.X. Still, we suggest you to
[upgrade the agents]

Stop `temboard` service:

``` shell
sudo systemctl stop temboard
```

Update temboard package with your [preferred installation method].

The database structure hasn't changed in this release, however temBoard now
requires to version the schema and checks it at startup. This will ease future
updates a lot.

The `repository` database schema must be stamped to the latest version with:

``` shell
sudo -u temboard temboard-migratedb stamp
```

Start `temboard` service:

```shell
sudo systemctl start temboard
```
### Upgrade `4.x` to `5.0`

Stop `temboard` service:
```shell
sudo systemctl stop temboard
```

New package installation:
```shell
sudo yum install temboard
```

Upgrade `repository` database schema:

```shell
curl https://raw.githubusercontent.com/dalibo/temboard/master/share/sql/upgrade-4-5.sql | sudo -u postgres psql temboard
```

or

```shell
sudo -u postgres psql -U postgres -1 -f \
     /usr/share/temboard/sql/upgrade-4-5.sql temboard
```

To enable monitoring data purge policy, you need to update `temboard.conf` by
adding the `[monitoring]` section and configure `purge_after` parameter. This
parameter configures the amount of monitoring data, expressed in day, to keep
in the repository. The purge policy is applied every 24 hours.

Start `temboard` service:
```shell
sudo systemctl start temboard
```

**Pull mode**

Version 5 comes with a new way to collect monitoring data from the agents.
Before this version, agents were pushing monitoring data to temboard server.
Starting from version 5, temboard server is now able to pull monitoring data
if the target agent has been deployed in version 5 or upper. The server still
supports push mode for the agents still running in version 4.

### Upgrade `3.0` to `4.0`

Stop `temboard` service:
```shell
sudo systemctl stop temboard
```

New package installation:
```shell
sudo yum install temboard
```

Upgrade `repository` database schema:

```shell
sudo -u postgres /usr/pgsql-10/bin/psql -U postgres -f \
     /usr/share/temboard/sql/upgrade-3.0-4.0.sql temboard
```

Update `temboard.conf` by adding the `[notifications]` section. Please see
[this HOWTO](temboard-howto-alerting.md#notifications) for more informations.

Start `temboard` service:

```shell
sudo systemctl start temboard
```

### Upgrade `2.x` to `3.0`

Stop `temboard` service:
```shell
sudo systemctl stop temboard
```

New package installation:
```shell
sudo yum install temboard
```

Load the maintenance plugin by adding `"maintenance"` in the list of plugins in
your `temboard.conf` file.

Upgrade `repository` database schema:

```shell
sudo -u postgres /usr/pgsql-10/bin/psql -U postgres -f \
     /usr/share/temboard/sql/upgrade-2.2-3.0.sql temboard
```

Start `temboard` service:
```shell
sudo systemctl start temboard
```

Activate the maintenance plugin for the instances in the settings view in
your browser.

### Upgrade `1.2` to `2.0`

Stop `temboard` service:
```shell
sudo systemctl stop temboard
```

New package installation:
```shell
sudo yum install temboard
```

Upgrade `repository` database schema:

```shell
sudo -u postgres /usr/pgsql-10/bin/psql -U postgres -f \
     /usr/share/temboard/sql/alerting.sql temboard
sudo -u postgres /usr/pgsql-10/bin/psql -U postgres -f \
     /usr/share/temboard/sql/upgrade-1.2-2.0.sql temboard
```

Start `temboard` service:
```shell
sudo systemctl start temboard
```
### Upgrade `1.1` to `1.2`

Stop `temboard` service:
```shell
sudo systemctl stop temboard
```

New package installation:
```shell
sudo yum install temboard
```

Start `temboard` service:
```shell
sudo systemctl start temboard
```

### Upgrade `0.0.1` to `1.1`

`temboard` upgrade process is going to be done within 4 stages:

* Software upgrade
* Configuration update
* Repository upgrade
* Post-upgrade operations

**Software upgrade**

First, `temboard` must be stopped:
```shell
sudo systemctl stop temboard
```

New package installation:
```shell
sudo yum install temboard
```

**Configuration update**

The following changes should be reflected into the configuration file:

* plugin `supervision` renamed to `monitoring` : parameters `plugins` and `plugins_orm_engine`
* plugin `settings` renamed to `pgconf` : parameter `plugins`
* CA cert. file not required anymore : parameter `ssl_ca_cert_file` can be commented

**Repository upgrade**

`temboard` database structure needs to be upgraded too. Before doing anything, you should make a backup of `temboard` database with `pg_dump`.

Once the backup is done, you can proceed with database upgrade:

* Load SQL script `/usr/share/temboard/sql/monitoring.sql` with super-user privileges
* Load upgrade script `/usr/share/temboard/sql/upgrade-0.0.1-1.1.sql` with super-user privileges

If everything goes well, you can drop old data:
```sql
DROP SCHEMA supervision CASCADE;
```

**Post-upgrade operations**

Task list clean-up:
```shell
sudo rm /var/run/temboard/task_list
```

Finally, `temboard` can be started:
```shell
sudo systemctl start temboard
```
