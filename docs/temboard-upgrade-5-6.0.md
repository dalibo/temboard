# Upgrade `5.X` to `6.0`

temBoard UI 6.0 is compatible with agent 5.X. Still, we suggest you to [upgrade
agents to
6.0](https://temboard.readthedocs.io/projects/agent/en/v6/upgrade.html#x-to-6-0).


Stop `temboard` service:

``` shell
sudo systemctl stop temboard
```

Update temboard package with your [preferred installation
method](installation.md#installation).

The database structure hasn't changed in this release, however temBoard now
requires to version the schema and checks it at startup. This will ease future
updates a lot.

The `repository` database schema must be stamped to the latest version with:

``` shell
$ sudo -u temboard temboard-migratedb stamp
```

Start `temboard` service:

```shell
sudo systemctl start temboard
```
