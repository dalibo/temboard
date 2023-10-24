mkdir -p "/var/lib/postgresql/archive"

docker_process_sql <<EOF
ALTER SYSTEM SET max_wal_senders TO '10';
ALTER SYSTEM SET archive_mode TO 'ON';
ALTER SYSTEM SET archive_command TO '/bin/cp -nv %p /var/lib/postgresql/archive/%f';
ALTER SYSTEM SET restore_command TO '/bin/cp -nv /var/lib/postgresql/archive/%f %p';
EOF

cat >> "$PGDATA/pg_hba.conf" <<EOF
host replication $POSTGRES_USER 0.0.0.0/0 md5
EOF
