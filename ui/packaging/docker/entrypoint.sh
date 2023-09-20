#!/bin/bash -eu

export PGHOST=${PGHOST-localhost}
export PGPORT=${PGPORT-5432}
export PGUSER=${PGUSER-postgres}
PGPASSWORD=${PGPASSWORD-}
export PGDATABASE=${PGDATABASE-$PGUSER}

wait-for-it "${PGHOST}:${PGPORT}"
if [ ! -f /etc/temboard/temboard.conf ] ; then
	if ! DEBUG=y PGPASSWORD="$PGPASSWORD" /usr/share/temboard/auto_configure.sh; then
		cat /var/log/temboard-auto-configure.log >&2
		exit 1
	fi
fi

# Clean PG* used for setup. libpq for temBoard is configured only by config
# file.
# shellcheck disable=2086
unset ${!PG*}

set -x
exec sudo -EHu temboard "${@-temboard}"
