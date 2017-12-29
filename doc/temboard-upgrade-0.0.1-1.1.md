# Upgrade `0.0.1` to `1.1` (RHEL/CentOS)

`temboard` upgrade process is going to be done within 4 stages:

* Software upgrade
* Configuration update
* Repository upgrade
* Post-upgrade operations

## Software upgrade

First, `temboard` must be stopped:
```shell
sudo systemctl stop temboard
```

New package installation:
```shell
sudo yum install temboard
```

## Configuration update

The following changes should be reflected into the configuration file:

* plugin `supervision` renamed to `monitoring` : parameters `plugins` and `plugins_orm_engine`
* plugin `settings` renamed to `pgconf` : parameter `plugins`
* CA cert. file not required anymore : parameter `ssl_ca_cert_file` can be commented

## Repository upgrade

`temboard` database structure needs to be upgraded too. Before doing anything, you should make a backup of `temboard` database with `pg_dump`.

Once the backup is done, you can proceed with database upgrade:

* Load SQL script `/usr/share/temboard/sql/monitoring.sql` with super-user privileges
* Load upgrade script `/usr/share/temboard/sql/upgrade-0.0.1-1.1.sql` with super-user privileges

If everything goes well, you can drop old data:
```sql
DROP SCHEMA supervision CASCADE;
```

## Post-upgrade operations

Task list clean-up:
```shell
sudo rm /var/run/temboard/task_list
```

Finally, `temboard` can be started:
```shell
sudo systemctl start temboard
```
