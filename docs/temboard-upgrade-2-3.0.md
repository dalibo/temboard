# Upgrade `2.x` to `3.0` (RHEL/CentOS)

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
$ sudo -u postgres /usr/pgsql-10/bin/psql -U postgres -f \
     /usr/share/temboard/sql/upgrade-2.2-3.0.sql temboard
```

Start `temboard` service:
```shell
sudo systemctl start temboard
```

Activate the maintenance plugin for the instances in the settings view in
your browser.
