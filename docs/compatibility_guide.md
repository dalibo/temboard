temBoard is designed to interact with many components: systemd, PostgreSQL,
agents, etc.

As we are trying to find the right balance between innovation and backward
compatibility, we define a comprehensive list of platforms and software that
we support for each version.

Temboard 10 is the current release.

Each minor release (e.g. `10.1`, `10.2`, etc.) is compatible with the following
components:

|                |                                            |
| -------------- | -------------------------------------------|
| Linux          | Debian 12 and 13, Ubuntu 22.04 and 24.04, RHEL 8, 9 and 10 |
| Python         | 3.9+                                       |
| Postgres       | 13 to 18                                   |
| Temboard Agent | 9.x and 10.x                                |

Additional notes:

* On RHEL8, the default python version is 3.6. Be sure to install `python39`.
* RHEL7 et Debian 11 (bullseye) are unsupported
* All PostgreSQL versions below 13.x are obsolete and unsupported
* It is highly recommended to upgrade PostgreSQL to the latest minor version of your
  current major version
