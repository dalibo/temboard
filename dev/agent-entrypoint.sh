#!/bin/bash -eux

export PIP_CACHE_DIR=/usr/local/src/temboard/dev/pip-cache
mkdir -p $PIP_CACHE_DIR
chown "$(id -u):$(id -g)" $PIP_CACHE_DIR
pip cache dir

pip install --ignore-installed --no-deps -e /usr/local/src/temboard/agent/
temboard-agent --version
chown -R "$(stat -c "%u:%g" "$0")" /usr/local/src/temboard/agent

if ! [ -f /etc/temboard-agent/signing-public.pem ] ; then
	# Copy dev signing key to prefetch UI key.
	mkdir -p /etc/temboard-agent/
	cp -v /usr/local/src/temboard/dev/signing-public.pem /etc/temboard-agent/
fi

exec /usr/local/src/temboard/agent/packaging/docker/entrypoint.sh "$@"
