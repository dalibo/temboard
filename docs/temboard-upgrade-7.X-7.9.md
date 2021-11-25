# Upgrade `7.X` to `7.9`

## Stop service

Stop `temboard` service:

``` shell
sudo systemctl stop temboard
```

## Update package

Update temboard package with your [preferred installation
method](installation.md#installation).

## Upgrade SQL procedures

Then apply `repository` database upgrade with the following command:

``` shell
$ sudo -u temboard temboard-migratedb upgrade
```

## Start service

Start `temboard` service:

```shell
sudo systemctl start temboard
```
