# Upgrade `1.2` to `2.0` (RHEL/CentOS)

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
     /usr/share/temboard/sql/alerting.sql temboard
$ sudo -u postgres /usr/pgsql-10/bin/psql -U postgres -f \
     /usr/share/temboard/sql/upgrade-1.2-2.0.sql temboard
```

Start `temboard` service:
```shell
sudo systemctl start temboard
```
