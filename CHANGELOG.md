# Changelog

## [3.0] - 2019-03-XX

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
