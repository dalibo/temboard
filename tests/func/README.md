# Functionnal tests

Functionnal tests are executed **outside** temboard process. UI is installed and
registered using regular tools : pip, dpkg or yum, auto_configure.sh, etc. A
real Postgres database is set up for the repository

Tests are written in Python with pytest. Tests use selenium to communicate with
the UI.

For development purpose, a `docker-compose.yml` file describe the setup to
execute functionnal tests almost like on Circle CI. The main entry point is
`run.sh` which is responsible to install temboard, configure it and call pytest
with selenium parameters.

``` console
$ docker-compose up
```

On failure, the main container, named `ui`, wait for you to enter it and debug.
Project tree is mounted at `/workspace`.

``` console
$ docker-compose exec ui /bin/bash
root@ccb2ec0d78cb# /workspace/tests/func/run.sh --pdb -x
…
```
