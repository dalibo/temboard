#!/bin/bash -eu

set -x

# Create postgres user matching postgres container one.
POSTGRES_UID=$(stat -c "%u" /var/lib/postgresql/data)
POSTGRES_GID=$(stat -c "%g" /var/lib/postgresql/data)
if ! getent passwd postgres &>/dev/null ; then
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

export PGHOST=${PGHOST-${TEMBOARD_HOSTNAME}}
export PGPORT=${PGPORT-5432}
export PGUSER=${PGUSER-postgres}
export PGPASSWORD=${PGPASSWORD-}
export PGDATABASE=${PGDATABASE-postgres}

conf=$(find /etc/temboard-agent -name temboard-agent.conf)
if [ -z "${conf}" ] ; then
	if ! PGHOST=/var/run/postgresql /usr/share/temboard-agent/auto_configure.sh "${TEMBOARD_UI_URL}" ; then
		cat /var/log/temboard-agent-auto-configure.log >&2
		exit 1
	fi
	conf="$(find /etc/temboard-agent -name temboard-agent.conf)"
fi

export TEMBOARD_CONFIGFILE="$conf"

if ! [ -f "${conf}.d/administration.conf" ] ; then
	# Hack to use docker instead of pg_ctl.
	mkdir -p "${conf}.d"
	if [ -x /usr/bin/docker ] ; then
		# Create docker group matching docker socket ownership.
		DOCKER_GID=$(stat -c "%g" /var/run/docker.sock)
		if ! getent group "${DOCKER_GID}" &>/dev/null ; then
			groupadd --system --gid "${DOCKER_GID}" docker-host
			adduser postgres docker-host
		fi

		network=$(docker inspect --format '{{ .HostConfig.NetworkMode }}' $HOSTNAME)
		links=($(docker inspect --format '{{ $net := index .NetworkSettings.Networks "'"${network}"'" }}{{range $net.Links }}{{.}} {{end}}' "$HOSTNAME"))
		links=("${links[@]%%:${TEMBOARD_HOSTNAME}}")
		PGCONTAINER="${links[*]%%*:*}"
		COMPOSE_SERVICE=$(docker inspect --format "{{ index .Config.Labels \"com.docker.compose.service\"}}" "$HOSTNAME")
		echo "Managing PostgreSQL container $PGCONTAINER." >&2

		cat > "${conf}.d/administration.conf" <<- EOF
		[administration]
		pg_ctl = /usr/local/bin/pg_ctl_temboard.sh ${PGCONTAINER} %s
		EOF
	else
		echo "Can't start/stop PostgreSQL." >&2

		cat > "${conf}.d/administration.conf" <<- EOF
		[administration]
		pg_ctl = /bin/false %s
		EOF
	fi
fi

register() {
	set -x

	wait-for-it localhost:2345 -t 60

	temboard-agent register \
		--host "${TEMBOARD_REGISTER_HOST-$COMPOSE_SERVICE}" \
		--port "${TEMBOARD_REGISTER_PORT-2345}" \
		--groups "${TEMBOARD_GROUPS-default}"
}

wait-for-it "${PGHOST}:${PGPORT}"
# Clean PG* used for setup. libpq for temBoard is configured only by config
# file.
# shellcheck disable=2086
unset ${!PG*}

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

set -x
exec sudo -Eu postgres "$@"
