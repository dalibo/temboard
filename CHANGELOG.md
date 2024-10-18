<h1>Changelog</h1>

<!--
CI release job extracts changes from this file and attaches them as GitHub release notes.
Ensure you use consistent title format.
-->

## 9.0.0

**Breaking changes**

- Replace instance groups and user groups by *Environment*.
  An instance must be in one and single environment.
- temBoard agent v8 can't register to temBoard UI v9.
  Use `temboard register` to register a new temBoard v8 agent on a temBoard v9 UI.
  Or upgrade agent to v9.
  temBoard UI v9 can still manage agent v8.
- Drop support for 7.x agents.
- Drop python 2.7 support.
- Drop rhel7 and buster support, minimum versions are now 6.0.2 for tornado
and 1.3.2 for sqlalchemy.
- Drop plugin hotplug. Just restart temBoard UI or agent.
- Drop daemonization. Use nohup or systemd.

**Other changes**

- Postgres 17 support.
- Visualize Plan with PEV2.
- Packages for Ubuntu 24.04 Noble.
- Fix deletion of host metrics when removing an instance of multi-instances host.
- agent: Recover admin shutdown, backend terminated, etc.
- Fix error handling in agent plugins.
- A lot of modernization : moved to Vue3, Bootstrap 5, Flask and ruff.
- A lot of UI tweaks & fixes.
- Accept editing instance even when agent is down.
- Improved postgresql.conf handling and error management.
- `temboard query-agent` command now accepts `--delete` and `--post` to set HTTP verb.
- Improve home dashboard performance.


## 8.2.1

Released: 15 november 2023

- Fix package upgrade and remove on RHEL and DEB.
- ui: purge.sh does not requires PGHOST or PGUSER.


## 8.2.0

Released: 14 november 2023

!!! info "Multiple groups of instances and groups of users"

    In temBoard 9.0, we plan to remove the ability to put an instance in several groups of instances
    or a group of instances in several groups of users.

    An instance will be attached to a single *Environment*
    and each *Environment* will be administred by a single group of users.

    temboard 8.2 warns you about instances and groups of instances matching these cases.
    Read [GitHub issue #1283](https://github.com/dalibo/temboard/issues/1283) for details.

**Global changes**

- Packages postinst don't start stopped systemd units.
- Docker tag `snapshot` points to last build.
- Docker image latest and `8` points to last stable tag.
- Release packages for Ubuntu 22.04 Jammy.


**UI changes**

- Fix missing service file in debian package.
- Fix plugin list according to agent configuration when editing an instance.
- Fix garbled select when editing offline instance.
- Fix detection of running systemd in `auto_configure.sh`.
- Fix content for popover content in /pgconf/configuration page.
- Allow to edit unavailable instance.
- Configure Content-Security-Policy header.
- Drop public schema from temboard role search_path.
- Ignore psqlrc in `create_repository.sh`.
- Accept temboard-agent-register from v7 agent.
- Transparently drop unused agent key.
- Link to instance dahsboard from Instances settings.
- Warn pending restart of a PostgreSQL instance in UI.
- Warn outdated agent.
- Warn about instance in multiple groups of instance.
- Warn about group of instance in multiple groups of users.

**Agent changes**

- Limit activity response to 300 longest queries (also for blocking and waiting endpoints).



## 8.1

[Released](https://blog.dalibo.com/2023/09/11/temboard-8.1-en.html): 11 september 2023


**UI & Agent changes**

- Remove stretch from packages and CI
- Fix logging on light terminal.
- Pin minor version of Python dependency in debian packages.
- Remove dependency on distutils.
- Disable 3DES and other loose SSL algorithmes.
- Supports PostgreSQL 16.


**UI changes**

- Fix PGDATA always empty in CSV inventory.
- Export comment in CSV inventory.
- Unquote PGDATA from CSV inventory.
- Fix missing schema in upgrade script.
- Debian package now use system psycopg2.
- Fix restart of temBoard when upgrading package.
- Add user-agent in about page.
- Internalize deps without virtualenv on debian package.
- No longer displays UNDEF items.
- Check DB connectivity only for serve and web command.

**Agent changes**

- Accept hostname down to 1 char long.
- Fix monitoring probe when the OS release includes a + sign.
- Auto reconnect PostgreSQL on connection lost in statements and maintenance
  endpoints.
- Improve displaying errors in log.


## 8.0

Released 14 november 2022.

!!! warning

    temBoard UI 8.0 is compatible with temBoard agent 7.11 to ease migration.
    Upgrade UI first and then upgrade agents one at a time.

    temBoard agent 8 is **NOT** compatible with temBoard UI 7.11.

    This release requires specific upgrade instructions.
    See [Server Upgrade](server_upgrade.md) and [Agent Upgrade](agent_upgrade.md) for details.


**Breaking changes**

- temBoard UI dropped support for Internet Explorer 8. You may have issues with
  browsers older than 5 years.
- Dropped support for PostgreSQL 9.5 and 9.4. For both UI and agent.
- Dropped key-only authentication on agent. Access to UI grants full access on managed agent.
- New CLI for both UI and agent. `temboard` and `temboard-agent` are the single CLI entrypoints.
    - Removed `temboard --debug` CLI option.
    - Dropped commands `temboard-agent-adduser` and `temboard-agent-password`.
    - Commands `temboard-migratedb`, `temboard-agent-register` are moved as
        subcommands of `temboard` and `temboard-agent`.
- temBoard UI dropped push-metrics handler from pre-6.0 push metric collect.
- temBoard UI RPM does not execute `auto_configure.sh` upon installation.
- temBoard UI RPM does not create `temboard` UNIX user. Use auto_configure.sh
  instead.
- temBoard Agent RPM does not create `postgres` UNIX user. Use PostgreSQL packages instead.
- Packages does not provide logrotate configuration anymore. temBoard can still
  log to file.
- pg_ctl agent parameter must **not** be quoted now, in temboard-agent.conf.
- Agent auto_configure.sh now requires a parameter: the UI url.
- temBoard agent does not provide legacy single-installation systemd unit file
  `temboard-agent.service` in favor of `temboard-agent@.service`.
- temBoard agent debian package does not provide legacy `temboard-agent.init`
  SysV script. Use sytemd instead.
- temBoard agent auto_configure.sh now generates a single configuration file
  instead of `temboard-agent.conf.d/auto.conf`.
- temBoard agent auto_configure.sh does not configure file logging anymore.
- Dropped temBoard agent HTTP endpoint `/monitoring/probe/*`, some
  `/dashboard/` probes and more. Use `temboard routes` and `temboard-agent
  routes` to inspect availables HTTP URLs.
- Docker image for agent now configures agent with `auto_configure.sh`.
  temBoard agent configuration moved from `/etc/temboard-agent` to
  `/etc/temboard-agent/<cluster_name>`.


**Deprecation**

- Running temBoard UI with Python 2.7 and Python 3.5 is deprecated. All RPM and
  deb packages ships with Python 3.
- Debian stretch support is deprecated (EOL June 2022).


**New Features**

- PostgreSQL 15 support.
- Unified authentication. Signing in UI open full DBA access to agents, without
  double login.
- Register instance without querying UI API using `temboard register-instance`.
- Download instance inventory as CSV.
- Automatically refresh introspection data from agent.
- New *About temBoard* page with detailed installation's informations.
- New *About instance* page with PostgreSQL, system and agent informations.
- OpenMetrics endpoint. Accessible using temBoard UI as authenticating proxy to
  agent.
- RHEL9, Debian Bookworm (testing) packages.
- Increase agent OOM score with systemd.
- Restyled documentation with improved search and navigation.


**Changes**

- Each temBoard release has it's own docker tag. e.g. dalibo/temboard:8.0,
  dalibo/temboard:8.0rc1, etc. See Docker Hub repositories [dalibo/temboard]
  and [dalibo/temboard-agent].
- Streamlined docker images, basing on Debian Bullseye, with temBoard installed
  with APT instead of pip.
- Restart scheduler and worker pool background processes on crash.
- Improved error logging. Log format is now Postgres-like.

[dalibo/temboard]: https://hub.docker.com/repository/docker/dalibo/temboard
[dalibo/temboard-agent]: https://hub.docker.com/repository/docker/dalibo/temboard-agent


**UI changes**

- Sign agent requests with an asymetric cryptographic key. New agent does not
  require double authentification anymore.
- New command `temboard generate-key` for generating signing key.
- New database migration engine. Dropped dependency on Alembic, Mako, etc.
- Move `temboard-migratedb` as `temboard migratedb` subcommand.
- New command `temboard tasks flush` to flush old tasks when upgrading.
- Fast collect of monitoring and statements metrics upon agent registration.
- Format PostgreSQL start time in dashboard as relative date.
- temBoard UI waits for locks in monitoring collect. Abort long collect
  task. New parameter `[monitoring] collect_max_duration`.
- temBoard UI now has API key authorization, use for /metrics proxy to agent.
- New temBoard UI parameter `[auth] allowed_ip` to restrict API Key
  authorization. By default, only 127/8 is allowed.
- Improved refresh error handling in dashboard, activity and home page. Error
  are now inlined instead of modal.
- temBoard UI now accept to serve plain HTTP. For development purpose.
- New commands `temboard query-agent`, `temboard routes`, `temboard tasks
  run`, `temboard tasks schedule` and `temboard web` for debugging.
- Handle SIGCHLD in temboard UI too. No more zombies.
- Limit activity view to 300 longest queries.


**Agent changes**

- Unified authentification: agent now uses UI as source of identity.
- Dropped `users` file and related configuration.
- New command `temboard-agent fetch-key` to accept UI signing key.
- New option: `[temboard] ui_url`, pointing to UI URL.
- auto_configure.sh conditionnaly enable statements plugins.
- Move `temboard-agent-register` as `temboard-agent register` subcommand.
- New command `temboard-agent discover` to introspect temBoard agent, system
  and PostgreSQL.
- Refresh discover data on startup and Postgres connection recovery.
- temBoard agent pools connections to PostgreSQL used by web API, reducing
  connections stress on PostgreSQL.
- Heavily reduction of connection opened by dashboard.
- Drop agent configuration `postgresql:instance` in favor of Postgres
  setting `cluster_name`.
- Add new unified sessions and detailed locks endpoint.
- temBoard agent now depends on cryptography and bottle.
- New subcommands `temboard-agent routes`, `temboard-agent tasks run` and
  `temboard-agent web` for debugging.
- Monitoring purge_after default value is now set to 730 (2 years), it was empty
  before (no limit).


## Older releases

### 7.11

Released on 2022-05-23

- Fix heap bloat probe.
- Fix statements not purged.
- Collect metrics by agent batch. Huge performance boost.
- Log HTTP request response time.
- Check agent key on registration.
- docker: New tag `7` for stable branch.
- docker: Reduce image size using multi-stage build.

**Agent:**

- docker: Fix build.
- docker: Properly stop container on failure.


### 7.10

Released on 2022-02-22

- Fix performances issues with monitoring.
- Show runtime libpq version in logs and --version.
- Authenticate with agent using both header and query arg. 8.0 will remove
  query arg auth.
- Packages for bullseye for both UI and agent.
- Drop jessie package.
- Always set application_name.

**Server:**

- Fix database ownership on creation.
- Fix first collector run failure on new agent.
- Fix tracebacks when an agent is down.
- Fix 'null' instance comment with auto register.
- Ship a /usr/share/temboard/sql/reassign.sql script to fix ownership.
- Define a shell to temboard UNIX user.
- Review defaults temBoard user groups.
- Optionnal performance tracing in temBoard UI logs.
- Moving to Python3 on stretch, buster and bullseye.
- Drop another tooltip breaking dropdown menu.
- Monitoring: Time SQL queries for archive and aggregation.
- `systemctl reload temboard` now reload temBoard configuration.

**Agent:**

- Fix database probes always executed on same database.
- Reduce reconnexion in monitoring probes.
- Explicitily requires psycopg2 2.7+ on debian.
- Ignore loopback and tmpfs file systems.
- Drop Python2 support
- Build RHEL8 package with RockyLinux 8.


### 7.9

Released on 2022-01-03

- Support PostgreSQL 14.
- Fix deadlock in monitoring.
- Fix UI glitches.
- Restructured documentation.
- Improved logging messages.
- Dropped Debian Jessie support.
- agent: Monitor only local filesystem size.
- agent: Set umask 027 in auto_configure.sh.
- agent: Details components version in `temboard-agent --version` output.
- agent: Fix sysv init script shipped on systemd by debian package.


### 7.6

Released on 2021-02-10

- Fix wrong column name in SQL for chartdata for rollback transactions
    (monitoring) [@pgiraud]

### 7.5

Released on 2021-01-12

- Return valid JSON if no result is returned by postgres (monitoring)
    [@pgiraud]

### 7.4

Released on 2020-12-15

- Take userid into account for statdata query [@pgiraud]
- Fix daterange picker behavior [@pgiraud]

### 7.3

Released on 2020-10-15

- Commit after alert processing [@bersace]

### 7.2

Released on 2020-09-29

**Fixed**

- Extension btree_gist is not required anymore [@pgiraud]
- Various packaging fixes [@dlax]

### 7.1

Released on 2020-09-29

**Fixed**

- Fixed bug in wheel generation [@pgiraud].

### 7.0

Released on 2020-09-28

**Added**

- Statements plugin by [@pgiraud] and [@dlax].
- Load `PG*` vars, by [@bersace].

**Changed**

- Improved performance of the home page (instances list), by [@pgiraud].
- Activity filters are kept, by [@pgiraud].
- Better support for history navigation in monitoring, by [@pgiraud].
- Don't highlight short idle_in_transaction queries, by [@pgiraud].
- Added comment field for instance settings, by [@pgiraud].
- Allow users to choose the refresh interval (whenever a date range picker is
  used), by [@pgiraud].
- Agent: support for RHEL/CentOS 6 has been dropped.
- Agent: support for RHEL/CentOS 8 has been added.

**Fixed**

- Agent scripts now use the Python interpreter of their installation, not the
  first found in env, by [@bersace].


### 6.2

Released on 2020-08-07


**Changed**

- Alembic version table is now hosted in `application` schema, by [@bersace].


**Fixed**

- Always using TLS even if set to False, by [@bersace].
- SMTP port misinterpreted, by [@bersace].
- Authenticate with empty login or password, by [@bersace].
- Double error with unserializable error in worker, by [@bersace].
- Test PG access by temboard role after repo creation, by [@l00ptr]

### 6.1

Released on 2020-06-15

Fixed compatibility with old Alembic 0.8.3 shipped on RHEL7, by [@bersace].


### 6.0

Released on 2020-06-15

This release requires a special step before restarting temBoard. Please read
[upgrade to 6.0] documentation.

[upgrade to 6.0]: server_upgrade.md


**Added**

- Full PostgreSQL 12 support, including monitoring and configuration, by [@pgiraud].
- Search config `temboard.conf` default config file in working directory by
  [@bersace].
- temBoard repository schema is now versionned, by [@bersace].
- Load external plugins from setuptools entrypoint `temboard.plugins`, by [@orgrim].
- Debian Buster testing & packaging, by [@bersace].
- Agent: `purge.sh` script to clean an agent installation, by [@bersace].

**Fixed**

- Double loading of legacy plugins, by [@bersace].
- Impossibility to delete instance with SQLAlchemy < 1, by [@pgiraud].
- Impossibility to schedule ANALYZE, VACCUM or REINDEX, by [@bersace].
- Fix list of scheduled tasks in maintenance plugin, by [@pgiraud].

**Changed**

- Default configuration file is not required, by [@bersace].
- Log error message when alert processing fails, by [@bersace].
- Agent: `auto_configure.sh` refuses to overwrite existing configuration, by
  [@bersace].


### 5.0

Released on 2020-04-16

**Added**

- Purge policy for monitoring data by [@julmon](https://github.com/julmon)
- Pull mode: temboard server can now pull monitoring data from the agents by [@julmon](https://github.com/julmon)

**Removed**

- Agent does not support push mode anymore [@julmon](https://github.com/julmon)

**Fixed**

- Performances improvements of asynchronous task management by [@julmon](https://github.com/julmon)

### 4.0

Released on 2019-06-26

**Added**

- Support for reindex on table and database by [@pgiraud](https://github.com/pgiraud)
- Support for analyze/vacuum for database by [@pgiraud](https://github.com/pgiraud)
- Send notifications by SMS or email on state changes by [@pgiraud](https://github.com/pgiraud)

**Changed**

- Allow to use either psycopg2 or psycopg2-binary by [@bersace](https://github.com/bersace)
- Monitoring shareable urls by [@pgiraud](https://github.com/pgiraud)
- Use `pg_version_summary` when possible by [@pgiraud](https://github.com/pgiraud)
- Database schema, please see the [upgrade documentation](server_upgrade.md)

**Removed**

- Removed user notifications from dashboard by [@pgiraud](https://github.com/pgiraud)

**Fixed**

- Prevent endless chart height increase on Chrome 75 by [@pgiraud](https://github.com/pgiraud)
- Restrict access to instance to authorized users by [@julmon](https://github.com/julmon)
- Remove monitoring data when removing an instance by [@pgiraud](https://github.com/pgiraud)
- Move `metric_cpu_record.time` to `BIGINT` by [@julmon](https://github.com/julmon)

### 3.0

Released on 2019-03-20

**Added**

- Full screen mode for home page by [@pgiraud](https://github.com/pgiraud)
- Full screen mode for dashboard by [@pgiraud](https://github.com/pgiraud)
- Limit double authentication to not read only APIs by [@pgiraud](https://github.com/pgiraud)
- Maintenance plugin by [@pgiraud](https://github.com/pgiraud)
- Collapsible sidebar by [@pgiraud](https://github.com/pgiraud)
- New monitoring probes: replication lag and connection, temporary files by [@julmon](https://github.com/julmon)
- UI functional tests by [@bersace](https://github.com/bersace)
- Support Tornado 4.4 and 5 by [@bersace](https://github.com/bersace)
- Add auto configuration script by [@bersace](https://github.com/bersace)
- Show number of waiting/blocking req in activity tabs by [@pgiraud](https://github.com/pgiraud)
- Show availability status on home page by [@pgiraud](https://github.com/pgiraud)

**Changed**

- Dashboard like home page by [@pgiraud](https://github.com/pgiraud)
- Improve activity views by [@pgiraud](https://github.com/pgiraud)
- Review web framework by [@bersace](https://github.com/bersace)
- Review debian packaging by [@bersace](https://github.com/bersace)

**Removed**

- `pg_hba.conf` and `pg_ident.conf` edition removed from `pgconf` plugin by [@pgiraud](https://github.com/pgiraud)

**Fixed**

- Avoid monitoring data to get stuck in agent sending queue by [@julmon](https://github.com/julmon)
- Documentation cleaning and updates by [@bersace](https://github.com/bersace)
- Limit useless `rollback` statements on read only queries (repository database) by [@pgiraud](https://github.com/pgiraud)


[@bersace]: https://github.com/bersace
[@orgrim]: https://github.com/orgrim
[@pgiraud]: https://github.com/pgiraud
[@dlax]: https://github.com/dlax
[@l00ptr]: https://github.com/l00ptr
