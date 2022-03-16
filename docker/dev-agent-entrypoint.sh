#!/bin/bash -eux

pip install -e /usr/local/src/temboard/agent/ psycopg2-binary hupper

exec /usr/local/bin/docker-entrypoint.sh "$@"
