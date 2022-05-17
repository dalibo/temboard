#!/bin/bash -eux

export PIP_CACHE_DIR=/usr/local/src/temboard/dev/pip-cache
mkdir -p $PIP_CACHE_DIR
chown "$(id -u):$(id -g)" $PIP_CACHE_DIR
pip cache dir

pip install -e /usr/local/src/temboard/agent/ psycopg2-binary hupper
chown -R "$(stat -c "%u:%g" "$0")" /usr/local/src/temboard/agent

exec /usr/local/bin/docker-entrypoint.sh "$@"
