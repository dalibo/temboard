#!/bin/bash
#
# Setup manual HA using official docker Postgres image;
#
# On initialisation: the instance with the lowest IP is elected as primary.
# initdb is called and docker/postgres-setup-replication.sh setup archive. The
# secondary is initialized with pg_basebackup.
#
# On restart, if the other node is primary, the postgres instance is recreated
# with pg_rewind.
#
# There is nothing like automatic failover. You can trigger manually a
# switchover with dev/switchover.sh script which will promote the secondary.


# shellcheck source=/dev/null
. /usr/local/bin/docker-entrypoint.sh

_ha_init_secondary() {
	echo "Waiting for $PEER_HOST to serve."
	export PGUSER="$POSTGRES_USER"
	export PGPASSWORD="$POSTGRES_PASSWORD"

	_retry psql -Aqt -h "$PEER_HOST" -c 'SELECT NULL'

	echo "Initializing PGDATA with pg_basebackup."
	pg_basebackup \
		-h "$PEER_HOST" -p 5432 -U $POSTGRES_USER \
		-D "$PGDATA" \
		--format=p \
		--write-recovery-conf \
		--wal-method=stream \
		--checkpoint=fast
}


_ha_setup() {
	docker_setup_env

	chown postgres:postgres /var/lib/postgresql/archive

	echo "Waiting for $PEER_HOST to have network."
	if ! peerhost="$(_retry getent hosts "$PEER_HOST")" ; then
		echo "$PEER_HOST down. Can't elect primary."
		exit 1
	fi

	if [ "$DATABASE_ALREADY_EXISTS" = "true" ] ; then
		if is_in_recovery=$(_retry env PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$PEER_HOST" -U "$POSTGRES_USER" -Aqt -c 'SELECT pg_is_in_recovery();') ; then
			if [ "$is_in_recovery" = "t" ] ; then
				echo "Restarting as primary."
			else
				echo "Rewind pgdata to failback."
				PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$PEER_HOST" -U "$POSTGRES_USER" -Aqt -c "SELECT pg_backup_start('docker-rewind');"
				trap _ha_stop_peer_backup INT EXIT TERM
				su-exec postgres pg_rewind \
					--source-server="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$PEER_HOST:5432/" \
					--target-pgdata="$PGDATA" \
					--write-recovery-conf \
					--no-ensure-shutdown
				_ha_stop_peer_backup
				trap - INT EXIT TERM
			fi
		else
			echo "$PEER_HOST does not respond. Restarting."
		fi
	else
		# Elect primary using IP.
		IFS=" " read -r _ winner _ < <( ( getent hosts "$HOSTNAME" ; echo "$peerhost"; ) | sort | head -1)
		if [ "${winner}" = "$HOSTNAME" ] ; then
			echo "Elected as primary."
			# replication is configured in
			# postgres-setup-primary.sh
		else
			echo "Elected as secondary."
			sleep 3
			_ha_init_secondary
		fi
	fi
}

_ha_stop_peer_backup() {
	PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$PEER_HOST" -U "$POSTGRES_USER" -Aqt -c "SELECT pg_backup_stop();"
}

_retry() {
	for i in {2..7} ; do
		if "$@" ; then
			return
		else
			echo "Retrying in one second, attempt #$i."
			sleep 1
		fi
	done

	"$@"
}

if [ -v PEER_HOST ] ; then
	_ha_setup
else
	echo 'PEER_HOST undefined. No HA setup.'
fi

# trigger docker-entrypoin.sh main
_main "$@"
