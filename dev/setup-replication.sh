# -*- mode: sh; sh-shell: bash -*-
#
# This script setups both primary and secondary docker service for streaming
# physical replication.
#
# Simply mount this script in /docker-init-entrypoint.d/ and define
# `PRIMARY_HOST` env var in secondary, pointing to primary service name.
#
# Tested with Postgres 13 and 9.6, excluding any other version. Easy test with:
#
# docker compose down -v ; docker compose up primary secondary
#

primary_psql() {
	psql -h "$PRIMARY_HOST" "$@"
}

check_primary_is_ready() {
	local query

	if initdb --version | grep -qF ' 9.' ; then
		query="SELECT DISTINCT 'SUCCESS' FROM pg_settings WHERE name = 'wal_level' AND setting = 'replica';"
	else
		query="SELECT DISTINCT 'SUCCESS' FROM pg_hba_file_rules WHERE database::TEXT = '{replication}' AND address IS NULL;"
	fi

	primary_psql -c "$query" | grep -q SUCCESS
}

if [ -z "${PRIMARY_HOST-}" ]; then
	cat >> "${PGDATA}/postgresql.conf" <<-EOF
	wal_level = replica
	max_wal_senders = 8
	max_replication_slots = 8
	EOF
	cat >> "$PGDATA/pg_hba.conf" <<-EOF
	host    replication     all             all            ${POSTGRES_HOST_AUTH_METHOD}
	EOF
	pg_ctl -D "$PGDATA" -w reload
else
	for i in {0..9} ; do
		if check_primary_is_ready ; then
			break
		elif [ $i -lt 6 ] ; then
			sleep $i
		else
			exit 1
		fi
	done

	# Avoid using --create-slot not in PostgreSQL 9.6
	slot="replication_$HOSTNAME"
	primary_psql -tc "SELECT pg_create_physical_replication_slot('$slot');"

	docker_temp_server_stop
	rm -rf "${PGDATA:?}"/*
	PGPASSWORD="${POSTGRES_PASSWORD}" pg_basebackup \
		--verbose \
		--host="${PRIMARY_HOST}" \
		--username="${POSTGRES_USER}" \
		-X stream \
		--checkpoint=fast \
		--pgdata="$PGDATA" \
		--slot="$slot" \
		--write-recovery-conf \
	;

	cat >> "$PGDATA"/postgresql.conf <<-EOF
	hot_standby = on
	EOF

	docker_temp_server_start
	echo "Secondary configured."
fi
