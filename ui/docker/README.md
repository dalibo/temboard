## temBoard

temBoard is a web application for managing clusters for PostgreSQL instances.

This docker image targets development environment and demo.

## Environment variables

`temboard.conf` is generated from environment variables.

- `TEMBOARD_COOKIE_SECRET`
- `TEMBOARD_SSL_CA`, `TEMBOARD_SSL_CERT` and `TEMBOARD_SSL_KEY` for HTTPS.
- `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` and `PGPASSWORD` for access to
  repository.

## Running the demo

To start the demo, run:
``` console
docker-compose -f ./docker-compose.yml -f ./docker-compose.pg_stat_statements.yml up
```

When you are done with your tests, you can stop the demo using:
``` console
docker-compose -f docker-compose.yml -f docker-compose.pg_stat_statements.yml down -v
```

## Updating Docker image

Docker Hub triggers a new build on each push on master. Refresh manually
temBoard image with:

``` console
$ make clean build push
```
