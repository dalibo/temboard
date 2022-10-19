This section explains how to upgrade a PostgreSQL instance monitored by a temBoard agent.

To upgrade to PostgreSQL instance hosting the *repository* database,
please go to the [Server Upgrade] section.

[Server Upgrade]: server_upgrade.md


## Minor Upgrade

PostgreSQL minor upgrades (e.g. from `10.3` to `10.4`) are very important
but they include only backward-compatible changes.

Therefore, you can simply upgrade your instance using the usual update process,
depending on which distribution you are using.

You dont need to restart temBoard agent nor edit its configuration.


## Major Upgrade

PostgreSQL major upgrades (e.g. from 13 to 14) will bring new features and improvements.

If you choose to migrate your data from your current instance to a new one listening to another port (or on another host),
then you can simply add a temboard-agent to this new instance.
However you will lose the history of the former one.

If you choose the *in-place upgrade*, you can keep the same agent.
You don't need to restart agent nor edit its configuration.
