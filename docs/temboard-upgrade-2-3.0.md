# Upgrade `2.x` to `3.0` (RHEL/CentOS)

Make sure the instances agents are also running version 3.

Load the maintenance plugin by adding `"maintenance"` in the list of plugins in
your `temboard.conf` file.

Do the same for each agent configuration file (ie. `temboard-agent.conf`).

Activate the maintenance plugin for the instances in the settings view in
your browser.
