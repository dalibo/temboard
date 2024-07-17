<h1>Contributing</h1>

Thanks for your interest in contributing to temBoard. temBoard is an open
source project welcoming contribution from idea to code and more.


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
- `ui/` - Python Tornado/Flask project for temBoard UI aka server.
    - `ui/temboardui/toolkit` - Shared library between agent and UI.
- `agent/` - Bare Python project for temBoard agent.
    - `agent/temboardagent/toolkit` - Symlink to toolkit in UI source tree.
- `dev/` - Development scripts and data.
  - `dev/bin/` - Development scripts.
- `docker/` - Quickstart Docker Compose file.
- `tests/` - Functional integration tests.

Python package is `temboardui` for temBoard UI and `temboardagent` for temBoard
agent.


## Development Requirements

You need the following software to develop temBoard:

- bash, git, make, psql.
- Docker Compose v2.
- Python 3.6 with `venv` module.
- NodeJS 20+ and npm for building some browser assets.


## Setup Development

Running development version of UI and agent requires two terminals, one for
each.

The `develop` make target
builds assets,
creates a virtual environment for Python 3.6,
installs temBoard UI, its requirements, development tools,
builds agent Docker image,
starts docker services and initializes temBoard database.

``` console
$ make develop
make venv-3.6
make[1] : on entre dans le répertoire « /home/.../src/dalibo/temboard »
python3.6 -m venv dev/venv-py3.6/
...
2020-03-24 17:09:05,937 [30557] [migrator        ]  INFO: Database is up to date.
Initialized role temboard and database temboard.
docker compose up -d
temboard_repository_1 is up-to-date
Creating temboard_instance_1 ... done
Creating temboard_agent_1    ... done


    You can now execute temBoard UI with dev/venv-py3.6/bin/temboard


$ dev/venv-py3.6/bin/temboard --debug
INFO:  app: Using config file /home/bersace/src/dalibo/temboard/temboard.conf.
INFO:  tornado: Enabling Tornado's autoreload.
14:42:13 temboardui[1145101] DEBUG:  app: Looking for plugin dashboard.
...
14:42:13 temboardui[1145101] INFO:  temboardui: Serving temboardui on http://0.0.0.0:8888
...
```

Go to [http://localhost:8888/](http://localhost:8888/) to access temBoard
running with your code!

You now need to run the agent. Open a second terminal to interact with the
agent and execute the following commands.

``` console
$ docker compose exec agent0 /bin/bash
root@91cd7e12ac3e:/var/lib/temboard-agent# sudo -Eu postgres temboard-agent
12:41:10 temboardagent[67] DEBUG:  app: Starting temboard-agent 9.0.dev0.
...
```

The agent is preregistered in UI, using host `0.0.0.0` and port `2345`. The
monitored Postgres instance is named `postgres0.dev`.

Beware that two Postgres instances are set up with replication. The primary
instance may be either postgres0 or postgres1. See below for details.


## Coding Style

An `.editorconfig` file configures whitespace and charset handling in various
programming language. The [EditorConfig]( http://editorconfig.org/#download)
site links to plugins for various editors. See `.editorconfig` for a
description of the conventions. Please stick to these conventions.

Python syntax must conform to ruff. CI checks new code with ruff.

Javascript and CSS syntax should conform to prettier. It is recommended to
configure your editor to automatically format on save. CI checks new code with
prettier.

Make sure to be in ui/ directory to first check if files are already formatted:

``` console
npx prettier --check .

```
If necessary, you can then format your file:
``` console
npx prettier --write temboardui/static/src/
```

You can optionally install `husky` pre-commit hooks.

``` console
cd ui
npm run install-husky
```

## Executing in debug mode

temboard and temboard-agent commands has a debug mode.
In debug mode, logs are verbose,
files change triggers an automatic restart of the process,
an unhandled exception drops in an interactive PDB debugger prompt.

Enable debug mode by setting DEBUG=y environment variable.
For agent, only long running commands have autoreload.


## psql for Monitored PostgreSQL

If you need to execute queries in monitored PostgreSQL instances, execute psql
inside the corresponding agent container using the following command:

``` console
$ docker compose exec agent0 psql
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
$ docker compose exec agent1 /bin/bash
root@91cd7e12ac3e:/var/lib/temboard-agent# sudo -Eu postgres temboard-agent
 INFO: Starting temboard-agent 8.0.dev0.
 INFO: Found config file /etc/temboard-agent/temboard-agent.conf.
2022-01-11 10:12:55,130 [ 1568] [app             ] DEBUG: Looking for plugin activity.
...
```

bash history is shared amongst these two containers.

In UI, the second agent is pre-registered with address 0.0.0.0 and port 2346 instead of 2345.
Second instance FQDN is `postgres1.dev`.

The script `dev/switchover.sh` triggers a switchover between the two postgres
instances. Executing `dev/switchover.sh` one more time restore the original
topology.


## Testing previous version

Compose project for development configures a stable agent named `agent-stable`.
This agent is preregistered in development UI.
Browse `postgres-stable` instance in UI to ensure temBoard UI is compatible with stable agent.

Access Postgres instance monitored by stable agent using the following compose
invocation:

``` console
$ docker compose exec agent-stable psql
psql (13.5 (Debian 13.5-0+deb11u1), server 13.7)
Type "help" for help.

postgres=#
```

## Connect to the repository database

The own Postgres instance of the temBoard UI is exposed on the 5432 port of
the host machine so that it can be accessed with:

``` console
$ PGPASSWORD=temboard psql -h localhost -U temboard temboard
```

Alternatively, it is also reachable with:

``` console
$ docker compose exec repository psql -U postgres temboard
psql (16.0)
Type "help" for help.

temboard=#
```

## Choosing PostgreSQL Version

You can change the version of the monitored PostgreSQL instance by overriding
image tag in `docker-compose.override.yml`.

``` yaml title="docker-compose.override.yml" linenums="1" hl_lines="5 8"
version: "3.8"

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


## Launching Multiple Agents

Default development environment instanciates two PostgreSQL instances and their
temBoard agents. Root Makefile offers two targets to help testing big scale
setup :

- `make mass-agents` loops from 2348 to 3000 and instanciates a PostgreSQL
  instance for each number and an agent to monitor it. Number is used as agent
  port. Each instanciation requires you to type `y` and Enter. This allows to
  throttle instanciations and to stop when enough instances are up.
- `make clean-agents` trashes every existing instances from 2348 to 3000,
  without interaction. **make clean-agents does not unregister agents!**


## Execute Unit Tests

Each UI and agent projects has its own unit tests battery.
Enable the virtualenv and use pytest to run unit tests:

``` console
$ . dev/venv-py3.6/bin/activate
$ pytest ui/tests/unit
...
==== 31 passed, 10 warnings in 1.10 seconds ======
$ pytest agent/tests/unit
...
=============== 6 passed in 0.25s ================
$
```


## Execute Integration Tests

The `tests/` directory contains a pytest project to tests UI and agent
integration using Selenium.

On Debian your UNIX user must be in the ssl-cert group to run the tests.
Be careful, the tests will use the local installation of temboard if it exists
instead of dev files. To run the tests locally it is better not to have temboard installed.

Execute these tests right from your virtualenv, using pytest:

``` console
$ . dev/venv-py3.6/bin/activate
$ pytest tests/
============================= test session starts ==============================
platform linux -- Python 3.6.8, pytest-7.0.1, pluggy-1.0.0 -- /home/bersace/src/dalibo/temboard/dev/venv-py3.6/bin/python3.6
cachedir: .pytest_cache
postgresql: 14 (/usr/lib/postgresql/14/bin)
sqlalchemy: 1.4.35
system: Debian GNU/Linux 11 (bullseye)
tornado: 6.1
libpq: 14.2
psycopg2: 2.9.3 (dt dec pq3 ext lo64)
temboard: 8.0.dev0 (/home/bersace/src/dalibo/temboard/dev/venv-py3.6/bin/temboard)
temboard-agent: 8.0.dev0 (/home/bersace/src/dalibo/temboard/dev/venv-py3.6/bin/temboard-agent)
rootdir: /home/bersace/src/dalibo/temboard/tests, configfile: pytest.ini
plugins: mock-3.6.1, cov-3.0.0, tornado-0.8.1, anyio-3.5.0
...
tests/test_00_setup_ui.py::test_temboard_version PASSED                  [ 12%]
...
tests/test_20_register.py::test_web_register PASSED                      [100%]

============================== 8 passed in 17.69s ==============================
$
```

`pytest tests/ --help` describes custom options `--pg-version` and
`--selenium`. Take care of the custom pytest report header, it shows which
temboard and temboard-agent binary is used, the bin directory of PostgreSQL and
more.

`pytest tests/ --fixtures` describes fixtures defined by tests/conftest.py.
Fixtures configure a postgres for monitoring, an agent and the UI in `workdir/`
prefix. This may help you write a new test.

Selenium standalone container runs a headless Xvfb server with noVNC enabled.
View live tests in your browser at http://localhost:7900/ .
Click the connect button and interract with the tested UI using the embedded Firefox.

Selenium container may be flaky. If you suspend your computer, you may have
timeout from selenium. Use `make restart-selenium` to workaround this.


## UI Database Schema Version

temBoard database is versionned.
A version is the name of a file in `temboardui/model/versions`.
Each file contains the code to execute to upgrade to this version.

To create a new version, put a new file in `temboardui/model/versions/`
prefixed with a discrete number following the last version. As of now, version
file must ends with `.sql` and contains valid PostgreSQL SQL.

That's all. Use `temboard migratedb` to check and upgrade temBoard repository.


## Building CSS and Javascript

temBoard UI mainly relies on Bootstrap. The CSS files are compiled with SASS.
ViteJS manages assets from `ui/temboardui/static/src`. ViteJS builds assets in
`ui/temboardui/static` directory.

Execute all the following commands in ui/ directory.

In case you want to contribute on the styles, first install the NodeJS dev
dependencies:

``` console
$ npm install
```

Then you can either build a dist version of the CSS:

``` console
$ npm run build
```

Or run dev server which watch changes on source files and hot-reload modules in
your browser:

``` console
$ npm run dev
```

Now restart temBoard UI configured with ViteJS dev server base URL from
environment variable `VITEJS`:

``` console
$ VITEJS=http://localhost:5173 temboard --debug
...
2022-08-23 10:40:57 CEST temboardui[2315935] DEBUG:  vitejs: Using ViteJS dev server at http://localhost:5173.
2022-08-23 10:40:57 CEST temboardui[2315935] DEBUG:  vitejs: Skip reading ViteJS manifest.
...
```

**Beware of CORS!** Depending on your browser product and version, you may hit
an unstyled page if CORS policy denies loading assets from ViteJS dev server.
Ensure you run temBoard in **plain HTTP** and that you access both temBoard and
ViteJS dev server on `localhost`.

All assets managed by ViteJS are hot reloaded, including CSS. ViteJS Hot reload
does not required reloading server-side.


## Editing Documentation

The documentation is written in Markdown and built with `mkdocs`.
Editing documentation requires Python 3.8.

``` console
$ dev/venv-py3.8/bin/mkdocs serve --file docs/mkdocs.yml
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

Try to use [semantic line breaks]:
split lines by idea instead of reflowing words.
This helps reading diff, handling conflicts when rebasing.

[semantic line breaks]: https://sembr.org/


## Building RHEL Package

Building RPM packages for RHEL and compatible clones requires Docker and Docker
Compose for isolation. Uploading to Dalibo Labs requires internal project
yum-labs and access.

UI and agent each has `packaging/rpm` directory with a Makefile and scripts to build RPM packages.
Use `build-rhel<version>` make target like this:

``` bash
make -C ui/packaging/rpm/ build-rhel9
```

Version can be either 9, 8 or 7.
`agent/packaging/rpm/Makefile` provides the same targets.

The builder script searches for wheels in `ui/dist/`
and if not found, tries to download wheel from PyPI.
Use top level `make dist` to generate wheels.


## Building Debian Package

Building debian packages requires Docker and Docker Compose for isolation. For
signing, you need the ``devscripts`` package and a GPG private key. For
uploading, you require ``dput``.

```
sudo apt install devscripts dput
```

Define environment variables `DEBFULLNAME` and `DEBEMAIL`. mkchanges.sh scripts
signs changes with your GPG key matching these environment variables.

Each UI and agent has `packaging/deb/` directory with a Makefile and scripts to
build packages. Use `build-<codename>` target like this:

``` bash
make -C ui/packaging/deb build-bullseye
```

`codename` is one of `bookworm`, `bullseye` or `buster`.
`agent/packaging/deb/Makefile` provides the same targets.

The builder script search for wheels in `ui/dist/`
and if not found, tries to download wheel from PyPI.
Use top level `make dist` to generate wheels.


## Investigate logs with lnav

[lnav] is an awesome tool to browse and analyze log files.
temBoard provides configuration for lnav to enhance experience.
`make develop` configures lnav for better analysis of PostgreSQL and temBoard logs.
Just run lnav on temBoard logs and you're good to go.

```
$ temboard |& lnav
```


## Releasing

Releasing a new version of temBoard requires write access to master branch on
[main repository](https://github.com/dalibo/temboard) and Dalibo Labs YUM and
APT repositories.

To release a new version:

- Checkout release branch : master for v8.
- Edit `ui/temboardui/version.py` and `agent/temboardagent/version.py` without
  committing. The version must be the same and follow [PEP440].
- Check, commit, tag and push using `make release`.

For stable release, you need write access to Dalibo Labs repositories:

- Wait for [CircleCI pipeline] to publish [GitHub releases].
- Download packages with `make download-packages`.
- Publish Debian and RPM packages with `make publish-packages`.

To release a v7 minor version, please follow [v7
documentation](https://temboard.readthedocs.io/en/v7/CONTRIBUTING/#releasing-the-server).

Don't forget to update [Compatibility Guide](compatibility_guide.md).

[CircleCI pipeline]: https://app.circleci.com/pipelines/github/dalibo/temboard
[GitHub releases]: https://github.com/dalibo/temboard/releases
[PEP440]: https://www.python.org/dev/peps/pep-0440/#version-scheme


## Throw Environment

`make clean` destroy virtual environments and docker services. Restart from
`make develop` as documented above. If you only need to trash services, use
docker compose as usual : `docker compose down -v`, running `make develop` will
restart them and configure the database.


[dalibo/temboard]: https://github.com/dalibo/temboard
