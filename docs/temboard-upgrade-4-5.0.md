# Upgrade `4.x` to `5.0` (RHEL/CentOS)

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
$ curl https://raw.githubusercontent.com/dalibo/temboard/master/share/sql/upgrade-4-5.sql | sudo -u postgres psql temboard
```

or

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

## Pull mode

Version 5 comes with a new way to collect monitoring data from the agents.
Before this version, agents were pushing monitoring data to temboard server.
Starting from version 5, temboard server is now able to pull monitoring data
if the target agent has been deployed in version 5 or upper. The server still
supports push mode for the agents still running in version 4.
