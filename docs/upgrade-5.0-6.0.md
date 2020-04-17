# Upgrade `5.0` to `6.0`

Stop `temboard` service:

``` shell
sudo systemctl stop temboard
```

New package installation:

``` shell
sudo yum install temboard
```

Stamp `repository` database schema to latest version:

``` shell
$ temboard-migratedb stamp
```

Start `temboard` service:

```shell
sudo systemctl start temboard
```
