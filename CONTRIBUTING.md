# Development Environment Setup

You can quickly set up a dev env with virtualenv and Docker Compose.

Get the temBoard and submodules sources:

```console
$ git clone --recursive https://github.com/dalibo/temboard.git
```

First, create a virtualenv for Python2.7, activate it. Then install temBoard and
pull docker images:

``` console
$ pip install -e . psycopg2-binary
...
$ docker-compose pull
```

Now, bootstrap development with `make devenv` and launch temBoard.

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

Go to https://127.0.0.1:8888/ to access temBoard runing with your code! An agent
is already set up to manage the PostgreSQL cluster of the UI.

If you want to trash development env, use `docker-compose down -v` and restart
from `make devenv`.


## Develop both UI and agent

In case you are working on the agent at the same time, here are some more
instructions otherwise you can jump to the next section.

Assuming that `temboard-agent` code is cloned along with temboard, create a
`docker-compose.override.yaml` file with the following content:

```
version: '2.4'

services:
  agent:
    environment:
      TEMBOARD_SSL_CA: /usr/local/src/temboard-agent/share/temboard-agent_ca_certs_CHANGEME.pem
      TEMBOARD_SSL_CERT: /usr/local/src/temboard-agent/share/temboard-agent_CHANGEME.pem
      TEMBOARD_SSL_KEY: /usr/local/src/temboard-agent/share/temboard-agent_CHANGEME.key
      TEMBOARD_MONITORING_SSL_CA_CERT_FILE: /usr/local/src/temboard/share/temboard_CHANGEME.pem
    volumes:
      - ../temboard-agent/:/usr/local/src/temboard-agent/
      - .:/usr/local/src/temboard/
    command: tail -f /dev/null
```

You can then run the `$ docker-compose up` command again.

Then in an other terminal, run the following commands:

```
$ docker-compose exec agent bash # enters the agent machine
# pip install -e /usr/local/src/temboard-agent/ # installs temboard-agent in dev mode
# sudo -u postgres temboard-agent
```

The last thing to do is to register the instance so that you don't have to do
it manually in the interface. In an other terminal, use the following commands:
```
$ docker-compose exec agent bash # enters the agent machine
# sudo -u postgres temboard-agent-register --host $TEMBOARD_REGISTER_HOST --port $TEMBOARD_REGISTER_PORT --groups default $TEMBOARD_UI_URL
```

## CSS

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


## Launching Multiple Agents

Default development environment instanciate a single PostgreSQL instance and
it's temBoard agent. Root Makefile offers two targets to help testing bigger
infrastructure :

- `make mass-agents` loops from 2345 to 2400 and instanciate a PostgreSQL
  instance and an agent to monitor it. Each instanciation requires you to type
  `y`. This allows to throttle instanciations and to stop when enough instances
  are up.
- `make clean-agents` trashes every existings instances from 2345 to 2400,
  without interaction. **Agent are not unregistered!**


# Coding style

A `.editorconfig` file is included at the root of the repository configuring
whitespace and charset handling in various programming language.
The [EditorConfig]( http://editorconfig.org/#download) site links to plugins for
various editors. See `.editorconfig` for a description of the conventions.
Please stick to this conventions.

Python syntax must conform to flake8. Our CI checks new code with flake8.


# Contribution Workflow

Fork the project, commit in a branch and open a new GithUb PR on
https://github.com/dalibo/temboard.


# Releasing

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
