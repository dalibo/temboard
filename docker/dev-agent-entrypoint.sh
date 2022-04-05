#!/bin/bash -eux

pip install -e /usr/local/src/temboard/agent/ psycopg2-binary hupper
chown -R "$(stat -c "%u:%g" "$0")" /usr/local/src/temboard/agent

exec /usr/local/bin/docker-entrypoint.sh "$@"
