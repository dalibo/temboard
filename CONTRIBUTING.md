# Contributing


[dalibo/temboard]: https://github.com/dalibo/temboard

## Reporting an Issue & Submitting a Patch

We use the [dalibo/temboard] project to track issue and review
contributions. Fork the main repository and open a PR against
`master` as usual.


## Editing Documentation

The documentation is written in markdown and built with `mkdocs`
``` console
$ pip install -r docs/requirements.txt
$ make docs
```

The documentation will be placed the `site` folder

You can also run `make docs-serve` in another terminal and point your web browser
at <http://0.0.0.0:8000/>.




---

## Development Environment Setup

You can quickly set up a dev env with virtualenv and Docker Compose. Running
development version of UI and agent requires two shells, one for the UI and one
for the agent.

Get temBoard UI and agent sources:

```console
$ git clone --recursive https://github.com/dalibo/temboard.git
$ cd temboard/
$ git clone --recursive https://github.com/dalibo/temboard-agent.git agent/
```

Then, create a virtualenv for Python2.7, activate it. Then install temBoard and
pull docker images:

``` console
$ pip install -e . psycopg2-binary
...
$ docker-compose pull
```

Then, bootstrap development with `make devenv`.

``` console
$ make devenv
...
2020-03-24 17:09:05,937 [30557] [migrator        ]  INFO: Database is up to date.
Initialized role temboard and database temboard.
docker-compose up -d
temboard_repository_1 is up-to-date
Creating temboard_instance_1 ... done
Creating temboard_agent_1    ... done

$ temboard --debug
...
2020-03-24 17:11:55,997 [ 3551] [temboardui      ]  INFO: Starting temBoard 4.0+master on Debian GNU/Linux 10 (buster).
...
2020-03-24 17:11:56,015 [ 3551] [temboardui      ]  INFO: Serving temboardui on https://0.0.0.0:8888
...
```

Go to https://127.0.0.1:8888/ to access temBoard running with your code!

You now need to run an agent and register it in UI. Open a second shell for
managing the agent and execute the following commands.

``` console
$ docker-compose exec agent /bin/bash
root@91cd7e12ac3e:/var/lib/temboard-agent# pip install -e /usr/local/src/temboard-agent/ psycopg2-binary hupper
root@91cd7e12ac3e:/var/lib/temboard-agent# sudo -u postgres hupper -m temboardagent.scripts.agent
 INFO: Starting temboard-agent 8.0.dev0.
 INFO: Found config file /etc/temboard-agent/temboard-agent.conf.
2020-08-11 14:29:45,834 [ 3769] [app             ] DEBUG: Looking for plugin activity.
...
```

Now register the agent in UI, using host `0.0.0.0`, port `2345` and key
`key_for_agent`. The monitored Postgres instance is named `postgres.dev`.


### Throw your development environment

If you want to trash development env, use `docker-compose down -v` and restart
from `make devenv`.


### Monitoring another version of PostgreSQL

You can change the version of the monitored PostgreSQL instance by overriding
docker image in `docker-compose.override.yml`.

``` yml
# file docker-compose.override.yml
version: "2.4"

services:
  postgres:
    image: postgres:9.5-alpine
```

Now apply changes with `make devenv`. Docker-compose will recreate `postgres`
and `agent` containers, thus you need to install and start the agent as
documented above.


### CSS

temBoard UI mainly relies on `Bootstrap`. The CSS files are compiled with
`SASS`.

In case you want to contribute on the styles, first install the nodeJS dev
dependencies:

```
npm install
```

Then you can either build a dist version of the css:
```
grunt sass:dist
```

Or build a dev version which will get updated each time you make a change in
any of the .scss files:
```
grunt watch
```


### Launching Multiple Agents

Default development environment instanciate a single PostgreSQL instance and
it's temBoard agent. Root Makefile offers two targets to help testing bigger
infrastructure :

- `make mass-agents` loops from 2345 to 2400 and instanciate a PostgreSQL
  instance and an agent to monitor it. Each instanciation requires you to type
  `y`. This allows to throttle instanciations and to stop when enough instances
  are up.
- `make clean-agents` trashes every existings instances from 2345 to 2400,
  without interaction. **Agent are not unregistered!**


---

## Coding style

An `.editorconfig` file is included at the root of the repository configuring
whitespace and charset handling in various programming language.
The [EditorConfig]( http://editorconfig.org/#download) site links to plugins for
various editors. See `.editorconfig` for a description of the conventions.
Please stick to this conventions.

Python syntax must conform to flake8. Our CI checks new code with flake8.


## Contribution Workflow

Fork the project, commit in a branch and open a new GithUb PR on
https://github.com/dalibo/temboard.


## Releasing the Server

Releasing a new version of temBoard requires write access to master on [main
repository](https://github.com/dalibo/temboard), [PyPI
project](https://pypi.org/project/temboard), [Docker Hub
repository](https://hub.docker.com/r/dalibo/temboard) and Dalibo Labs YUM and
APT repositories.

For the tooling, you need Git 1.8+, a recent setuptools with wheel. For
distribution packaging, see ad-hoc documentation in `packaging/`.

To release a new version:

- Checkout release branch (like v2).
- Choose the next version according to `PEP 440
  <https://www.python.org/dev/peps/pep-0440/#version-scheme>`_ .
- Update `temboardui/version.py`, without committing.
- Generate and push commit and tag with `make release`.
- Push Python egg to PyPI using `make upload`.
- Build and upload RPM package with `make -C packaging/rpm all push`.
- Build and upload Debian package with `make -C packaging/deb all push`.
- Ensure docs/installation.md points to matching version of agent.

## Releasing the Agent

Releasing a new version of temBoard agent requires write access to
master on [main repository](https://github.com/dalibo/temboard-agent),
[PyPI project](https://pypi.org/project/temboard-agent) and [Docker Hub
repository](https://hub.docker.com/r/dalibo/temboard-agent).

For the tooling, you need Git 1.8+, a recent setuptools with wheel, and
twine. For debian packaging, see below.

Please follow these steps:

-   Checkout the release branch, e.g. v2.
-   Choose the next version according to [PEP 440](https://www.python.org/dev/peps/pep-0440/#version-scheme) .
-   Update `temboardagent/version.py`, without committing.
-   Generate commit and tag with `make release`.
-   Push Python egg to PyPI using `make upload`.
-   Build and push RPM packages using `make -C packaging/rpm all push`.
-   Build and push debian packages using
    `make -C packaging/deb all push`.
-   Trigger docker master build from
    <https://hub.docker.com/r/dalibo/temboard-agent/~/settings/automated-builds/>.

## Other documentation for maintainers


Checkout the RPM packaging README for the agent:

https://github.com/dalibo/temboard-agent/blob/master/packaging/rpm/README.rst
