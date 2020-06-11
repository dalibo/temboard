# Upgrade `5.X` to `6.0`

Stop `temboard` service:

``` shell
sudo systemctl stop temboard
```

Update temboard package with your [preferred installation
method](installation.md#installation).


Stamp `repository` database schema to latest version:

``` shell
$ temboard-migratedb stamp
```

Start `temboard` service:

```shell
sudo systemctl start temboard
```
