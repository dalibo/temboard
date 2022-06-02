#!/bin/bash -eu
#
# This script initializes the database, with idempotence.
#
# Makefile docker/entrypoint.sh and auto_configure.sh execute this script. It
# creates a temboard role, a temboard database owned by it and uses
# temboard migratedb to initialize database. With DEV=1 environment variable, a
# development SQL script is executed after initialization to setup database for
# development.
#
# Configure libpq with PG* environment variables.
#
# Makefile calls this script as user with a TCP PGHOST, PGPASSWORD set. Every
# access to Postgres is through TCP.
#
# auto_configure.sh and docker/entrypoint.sh call this script as root.
# create_repository.sh uses sudo to access Postgres through UNIX socket.
#

if [ -n "${DEBUG-}" ] ; then
	set -x
fi

SQLDIR=$(readlink -m "$0/../sql/")
SYSUSER="${SYSUSER-temboard}"

export PGUSER=${PGUSER-postgres}
export PGHOST=${PGHOST-/var/run/postgresql}
psql=(psql -d "$PGUSER")

if [ -d "$PGHOST" ] ; then
	# If local, sudo to PGUSER.
	psql=(sudo -nEHu "${PGUSER}" "${psql[@]}")
fi

TEMBOARD_DATABASE=${TEMBOARD_DATABASE-temboard}
TEMBOARD_PASSWORD=${TEMBOARD_PASSWORD-temboard}

if ! "${psql[@]}" -c "SELECT 'SKIP' FROM pg_catalog.pg_user WHERE usename = 'temboard'" | grep -q SKIP ; then
    "${psql[@]}" -awc "CREATE ROLE temboard LOGIN PASSWORD '${TEMBOARD_PASSWORD}';"
fi

if ! "${psql[@]}" -c "SELECT 'SKIP' FROM pg_catalog.pg_database WHERE datname = '$TEMBOARD_DATABASE'" | grep -q SKIP ; then
     "${psql[@]}" -awc "CREATE DATABASE $TEMBOARD_DATABASE OWNER temboard;"
fi

# Now configure psql and temboard migratedb as temboard.
PGUSER=temboard
export PGPASSWORD="$TEMBOARD_PASSWORD"
export PGDATABASE="$TEMBOARD_DATABASE"

if getent passwd "$SYSUSER" &>/dev/null && [ "$(whoami)" != "$SYSUSER" ] ; then
	# Run as temboard UNIX user. Wipe environment, this requires properly
	# temboard.conf.
	runas=(sudo -inu "$SYSUSER")
else
	runas=()
fi

migratedb=(
	"${runas[@]}"
	"$(type -p temboard)"
	${TEMBOARD_CONFIGFILE+--config=$TEMBOARD_CONFIGFILE}
	migratedb
)

psql=(psql --set 'ON_ERROR_STOP=on' --pset 'pager=off')
if [ -d "$PGHOST" ] ; then
	# If local, sudo to temboard.
	psql=("${runas[@]}" "${psql[@]}")
fi

if ! "${migratedb[@]}" check ; then
    "${migratedb[@]}" upgrade
    if [ -n "${DEV-}" ] ; then
        "${psql[@]}" -f "$SQLDIR/dev-fixture.sql"
    fi
fi
