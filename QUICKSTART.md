# Quickstart

We provide `docker-compose.yml` file to quickly try temBoard with a few
PostgreSQL clusters. Requires docker-compose 1.10+ and docker engine 1.10+.

``` console
wget https://raw.githubusercontent.com/dalibo/temboard/master/docker/docker-compose.yml
docker-compose up
```

`docker-compose` will launch:

- a PostgreSQL instance for temboard owns data
- the temBoard UI
- four PostgreSQL instances exposed on ports 5432, 5433, 5434 and 5435.
- a temBoard agent for each instance exposed on port 2345, 2346, 2347, 2348.

temBoard UI is available on <https://0.0.0.0:8888/> with `admin` / `admin`
credentials. You can access PostgreSQL instance with user and password
`postgres`. For example with pgbench:

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
