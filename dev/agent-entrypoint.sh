#!/bin/bash -eux

chown -R "$(stat -c "%u:%g" "$0")" /usr/local/src/temboard/agent

if ! [ -f /etc/temboard-agent/postgres0/signing-public.pem ] ; then
	# Copy dev signing key to prefetch UI key. Don't bother whether we are
	# managing first or second instance.
	mkdir -p /etc/temboard-agent/postgres{0,1}
	cp -fv /usr/local/src/temboard/dev/signing-public.pem /etc/temboard-agent/postgres0
	cp -fv /usr/local/src/temboard/dev/signing-public.pem /etc/temboard-agent/postgres1
fi

# Presere uv PATH when sudoing as Postgres.
sed -i /secure_path/d /etc/sudoers
visudo -cf /etc/sudoers

uv sync
exec uv run /usr/local/src/temboard/agent/packaging/docker/entrypoint.sh "$@"
