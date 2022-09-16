# Changelog

## [8.0] - Unreleased

This release requires a database schema migration. Use temboard-migratedb
script to proceed.

- Unified authentification: agents now accepts UI as source of identity.
- New database migration engine.
- Removed parameter of `temboard --debug` CLI option.
- Improved error logging.
- Move `temboard-migratedb` as `temboard migratedb` subcommand.
- Move `temboard-agent-register` as `temboard-agent register` subcommand.
- New command `temboard generate-key` for generating signing key.
- New command `temboard-agent fetch-key` to accept UI signing key.
- New subcommands `temboard tasks flush` and `temboard-agent tasks flush`.
- New subcommands `temboard query-agent`, `temboard routes`, `temboard
  tasks run`, `temboard schedule`, `temboard web`, `temboard-agent routes`,
  `temboard-agent tasks run` and `temboard-agent web` for debugging.
- New command `temboard-agent discover` to introspect temBoard agent, system
  and PostgreSQL.
- New agent option: `[temboard] ui_url`, pointing to UI URL.
- New agent auto_configure.sh required parameter: UI URL.
- temBoard agent auto_configure.sh does not configure file logging anymore.
  temBoard UI & agent package does not ship logrotate file anymore. temBoard UI
  & agent can still log to file if you configure it to do so.
- temBoard agent packages does not ship mono-installation service file. Use
  `auto_configure.sh` and `temboard-agent@.service` instead.
- temBoard agent RPM packages does not ship `temboard-agent.conf` anymore. Use
  `auto_configure.sh` instead.
- temBoard agent deb does not ship `temboard-agent.init` anymore. Use systemd
  instead.
- Post install script of temBoard UI RPM does not execute auto_configure.sh.
- temBoard UI RPM does not create `temboard` UNIX user. Use auto_configure.sh
  instead.
- Fast collect of monitoring and statements metrics upon agent registration.
- temBoard UI dropped push-metrics handler from pre-6.0 push metric collect.
- Removed scripts `temboard-agent-adduser` and `temboard-agent-password`.
- Agent dropped users file and configuration.
- Python 2.7 and 3.5 support is deprecated and will be removed in next major
  release.
- Debian Stretch support is deprecated and will be removed in next major
  release.
- temBoard agent now depends on cryptography and bottle.
- temBoard agent pools connections to PostgreSQL used by web API, reducing
  connections stress on PostgreSQL.
- Download instance inventory as CSV.
- Format PostgreSQL start time in dashboard.
- Avoid modal for dashboard refresh error.
- temBoard agent auto_configure.sh conditionnaly enable statements plugins.
- temBoard agent auto_configure.sh now generates a single configuration file.
- Dropped temBoard agent HTTP endpoint /monitoring/probe/*.
- temBoard server waits for locks in monitoring collect. Abort long collect
  task. New parameter `[monitoring] collect_max_duration`.
- temBoard UI now has API key authorization, use for very few specific
  endpoint.
- New temBoard UI parameter `[auth] allowed_ip` to restrict API Key
  authorization. By default, only 127/8 is allowed.
- temBoard UI now accept to serve plain HTTP. For development purpose.
- Dropped support of Internet Explorer 8 and below.
- Out-of-band instance registration with new command `temboard
  register-instance`.
- Heavily reduction of connection opened by dashboard.
- New About instance page with detailed informations.
- Drop agent configuration `postgresql:cluster_name` in favor of Postgres
  setting `cluster_name`.
- Improved refresh error handling in dashboard, activity and home page. Error
  are now transient instead of modal.


## [7.11] - Unreleased

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


## [7.10] - 2022-02-22

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


## [7.9] - 2022-01-03

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


## [7.6] - 2021-02-10

- Fix wrong column name in SQL for chartdata for rollback transactions
    (monitoring) [@pgiraud]

## [7.5] - 2021-01-12

- Return valid JSON if no result is returned by postgres (monitoring)
    [@pgiraud]

## [7.4] - 2020-12-15

- Take userid into account for statdata query [@pgiraud]
- Fix daterange picker behavior [@pgiraud]

## [7.3] - 2020-10-15

- Commit after alert processing [@bersace]

## [7.2] - 2020-09-29

### Fixed

- Extension btree_gist is not required anymore [@pgiraud]
- Various packaging fixes [@dlax]

## [7.1] - 2020-09-29

### Fixed

- Fixed bug in wheel generation [@pgiraud].

## [7.0] - 2020-09-28

### Added

- Statements plugin by [@pgiraud] and [@dlax].
- Load `PG*` vars, by [@bersace].

### Changed

- Improved performance of the home page (instances list), by [@pgiraud].
- Activity filters are kept, by [@pgiraud].
- Better support for history navigation in monitoring, by [@pgiraud].
- Don't highlight short idle_in_transaction queries, by [@pgiraud].
- Added comment field for instance settings, by [@pgiraud].
- Allow users to choose the refresh interval (whenever a date range picker is
  used), by [@pgiraud].
- Agent: support for RHEL/CentOS 6 has been dropped.
- Agent: support for RHEL/CentOS 8 has been added.

### Fixed

- Agent scripts now use the Python interpreter of their installation, not the
  first found in env, by [@bersace].


## [6.2] - 2020-08-07


### Changed

- Alembic version table is now hosted in `application` schema, by [@bersace].


### Fixed

- Always using TLS even if set to False, by [@bersace].
- SMTP port misinterpreted, by [@bersace].
- Authenticate with empty login or password, by [@bersace].
- Double error with unserializable error in worker, by [@bersace].
- Test PG access by temboard role after repo creation, by [@l00ptr]

## [6.1] - 2020-06-15

Fixed compatibility with old Alembic 0.8.3 shipped on RHEL7, by [@bersace].


## [6.0] - 2020-06-15

This release requires a special step before restarting temBoard. Please read
[upgrade to 6.0] documentation.

[upgrade to 6.0]: server_upgrade.md


### Added

- Full PostgreSQL 12 support, including monitoring and configuration, by [@pgiraud].
- Search config `temboard.conf` default config file in working directory by
  [@bersace].
- temBoard repository schema is now versionned, by [@bersace].
- Load external plugins from setuptools entrypoint `temboard.plugins`, by [@orgrim].
- Debian Buster testing & packaging, by [@bersace].
- Agent: `purge.sh` script to clean an agent installation, by [@bersace].

### Fixed

- Double loading of legacy plugins, by [@bersace].
- Impossibility to delete instance with SQLAlchemy < 1, by [@pgiraud].
- Impossibility to schedule ANALYZE, VACCUM or REINDEX, by [@bersace].
- Fix list of scheduled tasks in maintenance plugin, by [@pgiraud].

### Changed

- Default configuration file is not required, by [@bersace].
- Log error message when alert processing fails, by [@bersace].
- Agent: `auto_configure.sh` refuses to overwrite existing configuration, by
  [@bersace].


## [5.0] - 2020-04-16

### Added

- Purge policy for monitoring data by [@julmon](https://github.com/julmon)
- Pull mode: temboard server can now pull monitoring data from the agents by [@julmon](https://github.com/julmon)

### Removed

- Agent does not support push mode anymore [@julmon](https://github.com/julmon)

### Fixed

- Performances improvements of asynchronous task management by [@julmon](https://github.com/julmon)

## [4.0] - 2019-06-26

### Added

- Support for reindex on table and database by [@pgiraud](https://github.com/pgiraud)
- Support for analyze/vacuum for database by [@pgiraud](https://github.com/pgiraud)
- Send notifications by SMS or email on state changes by [@pgiraud](https://github.com/pgiraud)

### Changed

- Allow to use either psycopg2 or psycopg2-binary by [@bersace](https://github.com/bersace)
- Monitoring shareable urls by [@pgiraud](https://github.com/pgiraud)
- Use `pg_version_summary` when possible by [@pgiraud](https://github.com/pgiraud)
- Database schema, please see the [upgrade documentation](server_upgrade.md)

### Removed

- Removed user notifications from dashboard by [@pgiraud](https://github.com/pgiraud)

### Fixed

- Prevent endless chart height increase on Chrome 75 by [@pgiraud](https://github.com/pgiraud)
- Restrict access to instance to authorized users by [@julmon](https://github.com/julmon)
- Remove monitoring data when removing an instance by [@pgiraud](https://github.com/pgiraud)
- Move `metric_cpu_record.time` to `BIGINT` by [@julmon](https://github.com/julmon)

## [3.0] - 2019-03-20

### Added

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

### Changed

- Dashboard like home page by [@pgiraud](https://github.com/pgiraud)
- Improve activity views by [@pgiraud](https://github.com/pgiraud)
- Review web framework by [@bersace](https://github.com/bersace)
- Review debian packaging by [@bersace](https://github.com/bersace)

### Removed

- `pg_hba.conf` and `pg_ident.conf` edition removed from `pgconf` plugin by [@pgiraud](https://github.com/pgiraud)

### Fixed

- Avoid monitoring data to get stuck in agent sending queue by [@julmon](https://github.com/julmon)
- Documentation cleaning and updates by [@bersace](https://github.com/bersace)
- Limit useless `rollback` statements on read only queries (repository database) by [@pgiraud](https://github.com/pgiraud)


[@bersace]: https://github.com/bersace
[@orgrim]: https://github.com/orgrim
[@pgiraud]: https://github.com/pgiraud
[@dlax]: https://github.com/dlax
[@l00ptr]: https://github.com/l00ptr
