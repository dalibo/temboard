# Changelog

## [6.0] - 2020-XX-XX

### Added

- Search config `temboard.conf` default config file in working directory by
  [@bersace].
- temBoard repository schema is now versionned, by [@bersace].
- Load external plugins from setuptools entrypoint `temboard.plugins`, by [@orgrim].
- Debian Buster testing & packaging, by [@bersace].

### Fixed

- Full PostgreSQL 12 support, including monitoring and configuration, by [@pgiraud].
- Double loading of legacy plugins, by [@bersace].

### Changed

- Default configuration file is not required, by [@bersace].
- Log error message when alert processing fails, by [@bersace].


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
- Database schema, please see the [upgrade documentation](temboard-upgrade-3.0-4.0.md)

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
