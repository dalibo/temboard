# Upgrade `6.X` to `7.0`

## Update agents

temBoard UI 7.0 is compatible with agent 6.X. Still, we suggest you to [upgrade
agents to
7.0](https://temboard.readthedocs.io/projects/agent/en/v7/upgrade.html#x-to-7-0).

*Note: An upgrade of the agent is required if you want to use the new `statements`
plugin.*

## Stop service

Stop `temboard` service:

``` shell
sudo systemctl stop temboard
```

## Update package

Update temboard package with your [preferred installation
method](installation.md#installation).

## Upgrade database structure

With the addition of the `statements` plugin, an upgrade of the repository
database schema is required.

First of all, please make sure that you first did the **upgrade from 5 to 6**.
This is very important!

Then apply `repository` database structure upgrade with the following command:

``` shell
$ temboard-migratedb upgrade
```

## Start service

Start `temboard` service:

```shell
sudo systemctl start temboard
```

## Activate statements plugin

Open temBoard in your browser and activate the `statements` plugin for the
different instances on which you want to use it.
