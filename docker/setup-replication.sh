if [ -z "${PRIMARY_HOST-}" ]; then
	cat >> "${PGDATA}/postgresql.conf" <<-EOF
	wal_level = hot_standby
	max_wal_senders = 8
	hot_standby = on
	EOF
	cat >> "$PGDATA/pg_hba.conf" <<-EOF
	host    replication     all             all            ${POSTGRES_HOST_AUTH_METHOD}
	EOF
	pg_ctl -D "$PGDATA" -w reload
else
	for j in {0..5} ; do
		if psql -h "$PRIMARY_HOST" -c "SELECT DISTINCT 'SUCCESS' FROM pg_hba_file_rules WHERE database::TEXT = '{replication}' AND address IS NULL;" | grep -q SUCCESS ; then
			break
		else
			sleep $j
		fi
	done

	docker_temp_server_stop
	rm -rf "${PGDATA:?}"/*
	PGPASSWORD="${POSTGRES_PASSWORD}" pg_basebackup \
		--verbose \
		--host="${PRIMARY_HOST}" \
		--username="${POSTGRES_USER}" \
		--wal-method=stream \
		--checkpoint=fast \
		--pgdata="$PGDATA" \
		--create-slot --slot="replication_$HOSTNAME" \
		--write-recovery-conf \
	;

	cat >> "${PGDATA}/postgresql.conf" <<-EOF
	primary_conninfo = 'host=${PRIMARY_HOST} port=5432 user=${POSTGRES_USER} password=${POSTGRES_PASSWORD}'
	EOF

	docker_temp_server_start
fi
