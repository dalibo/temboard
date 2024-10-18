temBoard is designed to interact with many components: systemd, PostgreSQL,
agents, etc.

As we are trying to find the right balance between innovation and backward
compatibility, we define a comprehensive list of platforms and software that
we support for each version.

Temboard 9 is the current release.

Each minor release (e.g. `9.1`, `9.2`, etc.) is compatible with the following
components:

|                |                                            |
| -------------- | -------------------------------------------|
| Linux          | Debian 11 and 12, Ubuntu 22.04 and 24.04, RHEL 8 and 9  |
| Python         | 3.6+                                       |
| Postgres       | 12 to 17                                   |
| Temboard Agent | 8.2 and 9.x                                |

Additional notes:

* RHEL7 et Debian 10 (buster) are obsolete and unsupported
* All PostgreSQL versions below 13.x are obsolete and unsupported
* It is highly recommended to upgrade PostgreSQL to the latest minor version of your
  current major version
