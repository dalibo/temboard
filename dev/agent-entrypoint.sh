#!/bin/bash -eux

export PIP_CACHE_DIR=/usr/local/src/temboard/dev/pip-cache
export PIP_BREAK_SYSTEM_PACKAGES=1
mkdir -p $PIP_CACHE_DIR
chown "$(id -u):$(id -g)" $PIP_CACHE_DIR
pip cache dir

pip install --ignore-installed --no-deps -e /usr/local/src/temboard/agent/
temboard-agent --version
chown -R "$(stat -c "%u:%g" "$0")" /usr/local/src/temboard/agent

if ! [ -f /etc/temboard-agent/postgres0/signing-public.pem ] ; then
	# Copy dev signing key to prefetch UI key. Don't bother whether we are
	# managing first or second instance.
	mkdir -p /etc/temboard-agent/postgres{0,1}
	cp -fv /usr/local/src/temboard/dev/signing-public.pem /etc/temboard-agent/postgres0
	cp -fv /usr/local/src/temboard/dev/signing-public.pem /etc/temboard-agent/postgres1
fi

exec /usr/local/src/temboard/agent/packaging/docker/entrypoint.sh "$@"
