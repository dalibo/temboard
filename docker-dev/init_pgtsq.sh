#!/bin/bash
set -e

# Configure shared_preload_libraries
echo "shared_preload_libraries = 'pg_track_slow_queries'" >> $PGDATA/postgresql.conf

# Restart PG
pg_ctl -D "$PGDATA" -w stop -m fast
pg_ctl -D "$PGDATA" -w start

# Create extension on postgres DB
psql -U postgres -d postgres -c "CREATE EXTENSION pg_track_slow_queries;"
