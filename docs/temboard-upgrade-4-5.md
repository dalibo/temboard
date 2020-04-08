# Upgrade `4` to `5` (RHEL/CentOS)

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
$ sudo -u postgres psql -U postgres -1 -f \
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
