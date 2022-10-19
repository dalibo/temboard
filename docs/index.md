
![temBoard](temboard.png)

temBoard is a powerful management tool for PostgreSQL. You can use it to monitor, optimize or configure multiple PostgreSQL instances.

temBoard is composed of 2 basic elements:

- A lightweight agent to install on every PostgreSQL server to monitor and
  manage.
# Features

- Manage hundreds of instances in one interface.
- Fleet-wide and per-instance dashboards.
- Monitor PostgreSQL with advanced metrics.
- Manage running sessions.
- Track bloat and schedule vacuum on tables and indexes.
- Track slow queries.
- Tweak PostgreSQL configuration.

All of this from a web interface.

![Dashboard](screenshots/instance-dashboard.png)


# Quickstart

You can run a complete testing environment based on Docker Compose,
follow the [QUICKSTART](quickstart.md) guide for more details.


# Install

temBoard requires Python 3 and supports PostgreSQL 9.6 to 15.
temBoard is composed of 2 services:

- A lightweight agent to install on every PostgreSQL server to monitor and manage.
- A central server controlling the agents, collecting metrics and presenting it on a web UI.


You can set up a complete testing environment based on docker,  follow the
[QUICKSTART](QUICKSTART.md) guide for more details.


For a regular installation, follow the [Installation guide](server_install.md).
