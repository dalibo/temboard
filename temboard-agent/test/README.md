# Temboard Agent functional tests

This directory contains functional tests for each plugin. To run these tests you'll need:
  * PostgreSQL binaries of the version you want the agent will be connected to when running the tests
  * `nosetests`

## `nosetests` installation

``` console
# pip install nosetests
```

## Run the tests

There are 3 environment variables that can be used to change the global behaviour (default values are set into `test/configtest.py`):
  * `TBD_PGBIN`: PostgreSQL binaries path
  * `TBD_PGPORT`: PostgreSQL TCP listen port
  * `TBD_WORKPATH`: Work path where temp data are stored

To run the whole test suite:
``` console
TBD_PGBIN="/path/to/pg/9.6/bin" TBD_WORKPATH="/tmp" python2.7 /usr/bin/nosetests -v test_*.py
```
