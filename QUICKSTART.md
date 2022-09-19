# Quickstart

We provide `docker-compose.yml` file to quickly try temBoard with a few
PostgreSQL clusters. Requires docker-compose 1.10+ and docker engine 1.10+.

``` console
wget https://raw.githubusercontent.com/dalibo/temboard/v7/docker/docker-compose.yml
docker-compose up
```

`docker-compose` will launch:

- a PG 13 cluster (exposed at 5432)
- a PG 12 cluster (exposed at 5433)
- a PG 10 cluster (exposed at 5434)
- a PG 9.6 cluster (exposed at 5435)
- a temBoard agent for each PG cluster
- a standard PG 13 cluster for the UI (not exposed)
- a container for temBoard UI

temBoard UI is available on <https://0.0.0.0:8888/> with `admin` / `admin`
credentials. The agents can be accessed with `alice` / `alice` or `bob` / `bob`.

You can access clusters with user and password `postgres`. For example with
pgbench:

``` console
$ export PGHOST=0.0.0.0 PGPORT=5432 PGUSER=postgres PGPASSWORD=postgres
$ psql -c 'CREATE EXTENSION IF NOT EXISTS pg_stat_statements'
$ createdb pgbench
$ pgbench -i pgbench
$ pgbench -c 8 -T 60 pgbench
```

## /!\\ DO NOT USE THIS IN PRODUCTION /!\\

temBoard docker images are designed for *testing* and *demo*. The SSL
certificate is *self-signed* and the default passwords are dumb and public.

temBoard agent is designed to run on same host as PostgreSQL which is
incompatible with Docker service-minded architecture. temBoard agent images
require *access to docker socket* to restart PostgreSQL, which you do not want
in production.

To deploy temBoard in a production environment, take some time to
read <http://temboard.rtfd.io>.
