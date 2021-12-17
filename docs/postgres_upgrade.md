# Upgrade PostgreSQL

This section explains how to upgrade a PostgreSQL instance when it is monitored
by a Temboard agent.

To upgrade to PostgreSQL instance hosting the `repository` database, please
go to the [Server Upgrade] section.

[Server Upgrade]: server_upgrade.md

## Minor upgrade

PostgreSQL minor upgrades ( e.g. from `10.3` to `10.4`) are very important but
they include only backward-compatible changes.

Therefore, you can simply upgrade your instance using the usual update process,
depending on which distribution you are using.


## Major upgrade

PostgreSQL major upgrades ( e.g. from 13 to 14 ) will bring new features and
improvements.

If you choose to migrate that your data from your current instance to a new
one listening to another port ( or on another host), then you can simply add
a temboard-agent to this new instance. However you will lose the history of
the former one.

If you choose the "in-place upgrade", you can keep the same agent. Just edit
the "instance properties" in the `/settings/instances` section of the server
in order to refresh the agent introspection of the Postgres instance.
