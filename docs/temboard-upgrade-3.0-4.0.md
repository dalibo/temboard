# Upgrade `3.0` to `4.0` (RHEL/CentOS)

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
$ sudo -u postgres /usr/pgsql-10/bin/psql -U postgres -f \
     /usr/share/temboard/sql/upgrade-3.0-4.0.sql temboard
```

Update `temboard.conf` by adding the `[notifications]` section. Please see [this HOWTO](temboard-howto-alerting.md#notifications) for more informations.

Start `temboard` service:
```shell
sudo systemctl start temboard
```
