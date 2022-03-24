# Contributing

Thanks for your interest in contributing to temBoard. temBoard is an open
source project open to contribution from idea to code and more.


## Submitting an Issue or a Patch

We use the [dalibo/temboard] GitHub project to track issues and review
contributions. Fork the main repository and open a pull request against
`master` branch as usual.


## Cloning the Repository

Get temBoard UI and agent sources in one single repository:

```console
$ git clone https://github.com/dalibo/temboard.git
$ cd temboard/
```


## Directories Overview

[dalibo/temboard] git repository contains a few sub-projects. Here is a quick
overview.

- `docs/` - Global mkdocs documentation sources.
- `ui/` - Python Tornado project for temBoard UI aka server.
    - `ui/temboardui/toolkit` - Shared library between agent and UI.
- `agent/` - Bare Python project for temBoard agent.
    - `agent/temboardagent/toolkit` - Symlink to toolkit in UI source tree.
- `perfui/` - Docker & Grafana project to visualize temBoard performances traces.
- `docker/` - Development and quickstart docker files.

Python package is `temboardui` for temBoard UI and `temboardagent` for temBoard agent.
agent.


## Development Requirements

You need the following software to contribute to temBoard:

- bash, git, make, psql.
- Docker Compose.
- Python 3.6 with `venv` module.
- NodeJS and npm for building some assets.


## Setup Development

Running development version of UI and agent requires two terminals, one for
each.

The `develop` make target creates a virtual environment for Python 3.6,
installs temBoard UI, its dependencies, development tools, starts docker
services and initializes temBoard database.

``` console
$ make develop
make venv-3.6
make[1] : on entre dans le répertoire « /home/.../src/dalibo/temboard »
python3.6 -m venv .venv-py3.6/
...
2020-03-24 17:09:05,937 [30557] [migrator        ]  INFO: Database is up to date.
Initialized role temboard and database temboard.
docker-compose up -d
temboard_repository_1 is up-to-date
Creating temboard_instance_1 ... done
Creating temboard_agent_1    ... done


    You can now execute temBoard UI with .venv-py3.6/bin/temboard


$ .venv-py3.6/bin/temboard --debug
 INFO: Starting temboard 8.0.dev0.
 INFO: Found config file /home/.../temboard/temboard.conf.
 INFO: Running on Debian GNU/Linux 11 (bullseye).
 INFO: Using Python 3.6.8 (/home/.../.cache/pyenv/versions/temboard-uoBqmXGk-py3.6/bin/python) and Tornado 4.4.3 .
 INFO: Using libpq 11.5, Psycopg2 2.8.6 (dt dec pq3 ext lo64) and SQLAlchemy 1.3.24 .
2022-03-16 14:08:06,425 temboardui[1593889]: [pluginsmgmt     ]  INFO: Loaded plugin 'dashboard'.
...
2022-03-16 14:08:06,489 temboardui[1593889]: [temboardui      ]  INFO: Serving temboardui on https://0.0.0.0:8888
...
```

Go to [https://127.0.0.1:8888/](https://127.0.0.1:8888/) to access temBoard
running with your code!

You now need to run the agent. Open a second terminal to interact with the
agent and execute the following commands.

``` console
$ docker-compose exec agent0 /bin/bash
root@91cd7e12ac3e:/var/lib/temboard-agent# sudo -u postgres hupper -m temboardagent.scripts.agent
 INFO: Starting temboard-agent 8.0.dev0.
 INFO: Found config file /etc/temboard-agent/temboard-agent.conf.
2020-08-11 14:29:45,834 [ 3769] [app             ] DEBUG: Looking for plugin activity.
...
```

The agent is preregistered in UI, using host `0.0.0.0`, port `2345` and key
`key_for_agent`. The monitored Postgres instance is named `postgres0.dev`.

Beware that two Postgres instances are set up with replication. The primary
instance may be either postgres0 or postgres1. See below for details.


## psql for Monitored PostgreSQL

If you need to execute queries in monitored PostgreSQL instances, execute psql
inside the corresponding agent container using the following command:

``` console
$ docker-compose exec agent0 sudo -iu postgres psql
psql (13.5 (Debian 13.5-0+deb11u1), server 14.1)
WARNING: psql major version 13, server major version 14.
         Some psql features might not work.
Type "help" for help.

postgres=#
```


## Playing with Replication

Two postgres instances are up with replication. You can execute a second agent
for it likewise:

``` console
$ docker-compose exec agent1 /bin/bash
root@91cd7e12ac3e:/var/lib/temboard-agent# sudo -u postgres hupper -m temboardagent.scripts.agent
 INFO: Starting temboard-agent 8.0.dev0.
 INFO: Found config file /etc/temboard-agent/temboard-agent.conf.
2022-01-11 10:12:55,130 [ 1568] [app             ] DEBUG: Looking for plugin activity.
...
```

bash history is shared amongst these two containers.

In UI, the seconde agent is pre-registered with address 0.0.0.0, port 2346
instead of 2345, with the same key `key_for_agent`. The instance FQDN is
`postgres1.dev`.

The script `docker/dev-switchover.sh` triggers a switchover between the two
postgres instances. Executing `docker/dev-switchover.sh` one more time restore
the original typology.


## Launching Multiple Agents

Default development environment instanciates two PostgreSQL instances and their
temBoard agents. Root Makefile offers two targets to help testing big scale
setup :

- `make mass-agents` loops from 2347 to 3000 and instanciate a PostgreSQL
  instance and an agent to monitor it. Each instanciation requires you to type
  `y` and Enter. This allows to throttle instanciations and to stop when enough
  instances are up.
- `make clean-agents` trashes every existing instances from 2347 to 3000,
  without interaction. **make clean-agents does not unregister agents!**


## Choosing PostgreSQL Version

You can change the version of the monitored PostgreSQL instance by overriding
image tag in `docker-compose.override.yml`.

``` yml
# file docker-compose.override.yml
version: "2.4"

services:
  postgres0:
    image: postgres:9.5-alpine &postgres_image

  postgres1:
    image: *postgres_image
```

Now apply changes with `make develop`. Docker-compose will recreate `postgres0`
and `agent0` containers, thus you need to start the agent as documented above.

Note that defining a different major version for postgres0 and postgres1 breaks
physical replication.


## Execute UI Unit Tests

Enable the virtualenv and use pytest to run unit tests:

``` console
$ . .venv-py3.6/bin/activate
$ pytest ui/tests/unit
...
==== 31 passed, 10 warnings in 1.10 seconds ======
$
```


## Execute UI Func Tests

Go to tests/func and run docker-compose:

``` console
$ cd ui/tests/func
ui/tests/func/$ docker-compose up --force-recreate --always-recreate-deps --renew-anon-volumes --abort-on-container-exit ui
...
```

Functionnal tests are executed **outside** temboard process. UI is installed and
registered using regular tools : pip, dpkg or yum, auto_configure.sh, etc. A
real Postgres database is set up for the repository

Tests are written in Python with pytest.

For development purpose, a `docker-compose.yml` file describes the setup to
execute functionnal tests almost like on Circle CI. The main entry point is
`tests/func/run.sh` which is responsible to install temboard, configure it and
call pytest.

On failure, the main container, named `ui`, waits for you to enter it and
debug. Project tree is mounted at `/workspace`.

``` console
ui/tests/func/$ docker-compose exec ui /bin/bash
[root@ccb2ec0d78cb workspace]# tests/func/run.sh --pdb -x
…
```


## Coding Style

An `.editorconfig` file configures whitespace and charset handling in various
programming language. The [EditorConfig]( http://editorconfig.org/#download)
site links to plugins for various editors. See `.editorconfig` for a
description of the conventions. Please stick to these conventions.

Python syntax must conform to flake8. CI checks new code with flake8.


## UI Database Schema Version

temBoard repository is versionned. A version is the name of a file in
`temboardui/model/versions`. Each file contains the code to execute to upgrade
to this version.

To create a new version, put a new file in `temboardui/model/versions/`
prefixed with a discrete number following the last version. As of now, version
file must ends with `.sql` and contains valid PostgreSQL SQL.

That's all. Use temboard-migratedb to check and upgrade temBoard repository.


## Building CSS and Javascript

temBoard UI mainly relies on Bootstrap. The CSS files are compiled with SASS.
Execute all the following commands in ui/ directory.

In case you want to contribute on the styles, first install the nodeJS dev
dependencies:

``` console
$ npm install
```

Then you can either build a dist version of the CSS:

``` console
$ grunt sass:dist
```

Or build a dev version which will get updated each time you make a change in
any of the .scss files:

``` console
$ grunt watch
```


## Editing Documentation

The documentation is written in Markdown and built with `mkdocs`.

``` console
$ .venv-py3.6/bin/mkdocs serve
INFO     -  Building documentation...
INFO     -  Cleaning site directory
INFO     -  The following pages exist in the docs directory, but are not included in the "nav" configuration:
              - alerting.md
              - postgres_upgrade.md
INFO     -  Documentation built in 0.42 seconds
INFO     -  [16:21:24] Serving on http://127.0.0.1:8000/
...
```

Go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to view the
documentation. mkdocs has hot reload: saving file triggers a refresh in your
browser.


## Building Snapshot Package

You can build a RPM or deb snapshot like this:

``` console
$ make dist
$ make -C ui/packaging/rpm build-rhel8
$ make -C agent/packaging/deb build-buster
```

Find packages in `ui/dist` or `agent/dist` directories. See further targets in
`{ui,agent}/packaging/{deb,rpm}/Makefile`.


## Releasing the Server

Releasing a new version of temBoard requires write access to master on [main
repository](https://github.com/dalibo/temboard), [PyPI
project](https://pypi.org/project/temboard), [Docker Hub
repository](https://hub.docker.com/r/dalibo/temboard) and Dalibo Labs YUM and
APT repositories.

For the tooling, you need Git 1.8+, a recent setuptools with wheel. For
distribution packaging, see ad-hoc documentation in `ui/packaging/`.

To release a new version:

- Move to ui/ directory.
- Checkout release branch (like v2).
- Choose the next version according to [PEP 440]
  (https://www.python.org/dev/peps/pep-0440/#version-scheme).
- Update `temboardui/version.py`, without committing.
- Generate and push commit and tag with `make release`.
- Push Python egg to PyPI using `make upload`.
- Build and upload RPM package with `make -C packaging/rpm all push`.
- Build and upload Debian package with `make -C packaging/deb all push`.


## Releasing the Agent

Releasing a new version of temBoard agent requires write access to
master on [main repository](https://github.com/dalibo/temboard-agent),
[PyPI project](https://pypi.org/project/temboard-agent) and [Docker Hub
repository](https://hub.docker.com/r/dalibo/temboard-agent).

For the tooling, you need Git 1.8+, a recent setuptools with wheel, and
twine. For debian packaging, see below.

Please follow these steps:

- Move to agent/ directory.
- Checkout the release branch, e.g. v2.
- Choose the next version according to [PEP 440](https://www.python.org/dev/peps/pep-0440/#version-scheme) .
- Update `temboardagent/version.py`, without committing.
- Generate commit and tag with `make release`.
- Push Python egg to PyPI using `make upload`.
- Build and push RPM packages using `make -C packaging/rpm all push`.
- Build and push debian packages using
  `make -C packaging/deb all push`.
- Trigger docker master build from
  <https://hub.docker.com/r/dalibo/temboard-agent/~/settings/automated-builds/>.


## Throw Development Environment

`make clean` destroy virtual environments and docker services. Restart from
`make develop` as documented above. If you only need to trash services, use
docker-compose as usual : `docker-compose down -v`, running `make develop` will
restart them and configure the database.


[dalibo/temboard]: https://github.com/dalibo/temboard
