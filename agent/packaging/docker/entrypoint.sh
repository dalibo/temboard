#!/bin/bash -eu

set -x

export PGHOST="${PGHOST-/var/run/postgresql}"
export PGPORT=${PGPORT-5432}
export PGUSER=${PGUSER-postgres}
export PGPASSWORD=${PGPASSWORD-}
export PGDATABASE=${PGDATABASE-postgres}

# Create postgres user matching postgres container one.
if ! getent passwd postgres &>/dev/null ; then
	POSTGRES_UID=$(stat -c "%u" "${PGHOST}")
	POSTGRES_GID=$(stat -c "%g" "${PGHOST}")
	groupadd --system --gid "${POSTGRES_GID}" postgres
	useradd --system \
		--home-dir /var/lib/postgresql --no-create-home \
		--uid ${POSTGRES_UID} --gid postgres --shell /bin/bash \
		postgres
	if getent group ssl-cert &>/dev/null ; then
	    usermod --append --groups ssl-cert postgres
	fi
fi
chown -R postgres: ~postgres /etc/temboard-agent /var/lib/temboard-agent

# Wait until postgres is up
for _ in {10..0} ; do
	if  psql -Atc 'SELECT 1' ; then
		break
	else
		sleep 0.5
	fi
done

conf=$(find /etc/temboard-agent -name temboard-agent.conf)
if [ -z "${conf}" ] ; then

	if ! /usr/share/temboard-agent/auto_configure.sh "${TEMBOARD_UI_URL}" ; then
		cat /var/log/temboard-agent-auto-configure.log >&2
		exit 1
	fi
	conf="$(find /etc/temboard-agent -name temboard-agent.conf)"
fi

# Clean PG* used for setup. libpq for temBoard is configured only by config
# file.
# shellcheck disable=2086
unset ${!PG*}

export TEMBOARD_CONFIGFILE="$conf"

register() {
	set -x

	wait-for-it localhost:2345 -t 60

	temboard-agent register \
		--host "${TEMBOARD_REGISTER_HOST}" \
		--port "${TEMBOARD_REGISTER_PORT-2345}" \
		--environment "${TEMBOARD_ENVIRONMENT-default}"
}

if [[ "${*} " =~ "temboard-agent " ]] ; then
	hostportpath=${TEMBOARD_UI_URL#*://}
	hostport=${hostportpath%%/*}
	wait-for-it "${hostport}" -t 60

	if ! [ -f "${conf%/*}/signing-public.pem" ] ; then
		sudo -Eu postgres temboard-agent fetch-key
	fi

	# Always register, because signing key may be prefetched by dev
	# entrypoint.
	register &
fi

: "Agent environment ready. Running $*" >&2
exec sudo -Eu postgres "$@"
