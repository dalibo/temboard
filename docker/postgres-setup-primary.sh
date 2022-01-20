docker_process_sql <<EOF
CREATE ROLE secondary WITH LOGIN REPLICATION PASSWORD 'gobelet';
ALTER SYSTEM SET max_wal_senders TO '10';
ALTER SYSTEM SET archive_mode TO 'ON';
EOF

cat >> "$PGDATA/pg_hba.conf" <<EOF
host replication secondary 0.0.0.0/0 md5
EOF
