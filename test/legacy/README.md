# Temboard Agent functional tests

This directory contains functional tests for each plugin. To run these tests you'll need:
  * PostgreSQL binaries of the version you want the agent will be connected to when running the tests
  * `nosetests`

Those tests are intented to be run in CircleCI.

## `pytest` installation

``` console
# pip install pytest
```

## Run the tests

There are 3 environment variables that can be used to change the global behaviour (default values are set into `test/configtest.py`):
  * `TBD_PGBIN`: PostgreSQL binaries path
  * `TBD_PGPORT`: PostgreSQL TCP listen port
  * `TBD_WORKPATH`: Work path where temp data are stored

To run the whole test suite:
``` console
TBD_PGBIN="/path/to/pg/9.6/bin" TBD_WORKPATH="/tmp" pytest -v test/legacy/test_*.py
```

## Run the tests using docker

You can also run the tests via docker for several versions of Postgres.

```
docker-compose up
```
