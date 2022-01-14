#!/bin/bash -eu
#
# This script initialize the database, with idempotence.
#
# auto_configure.sh calls this script for production and Makefile for
# development.

if [ -n "${DEBUG-}" ] ; then
	set -x
fi

SQLDIR=$(readlink -m "$0/../sql/")

export PGUSER=${PGUSER-postgres}
export PGHOST=${PGHOST-/var/run/postgresql}
export PGDATABASE=${PGDATABASE-temboard}
TEMBOARD_PASSWORD=${TEMBOARD_PASSWORD-temboard}
psql=(psql -d postgres)

if [ -d "$PGHOST" ] ; then
	# If local, sudo to PGUSER.
	psql=(sudo -EHu "${PGUSER}" "${psql[@]}")
fi

if ! "${psql[@]}" -c "SELECT 'SKIP' FROM pg_catalog.pg_user WHERE usename = 'temboard'" | grep -q SKIP ; then
    "${psql[@]}" -awc "CREATE ROLE temboard LOGIN PASSWORD '${TEMBOARD_PASSWORD}';"
fi

if ! "${psql[@]}" -c "SELECT 'SKIP' FROM pg_catalog.pg_database WHERE datname = 'temboard'" | grep -q SKIP ; then
     "${psql[@]}" -awc "CREATE DATABASE temboard OWNER temboard;"
fi

if getent passwd temboard &>/dev/null ; then
	runas=(sudo -iu temboard)
else
	runas=()
fi

psql=(
	env "PGPASSWORD=$TEMBOARD_PASSWORD"
	psql -U temboard -d temboard -h "$PGHOST" -w
	--set 'ON_ERROR_STOP=on' --pset 'pager=off'
)
if [ -d "$PGHOST" ] ; then
	# If local, sudo to temboard.
	psql=("${runas[@]}" "${psql[@]}")
fi

unset PGUSER PGHOST PGDATABASE PGPASSWORD

if ! "${runas[@]}" temboard-migratedb check ; then
    "${runas[@]}" temboard-migratedb upgrade
    if [ -n "${DEV-}" ] ; then
        "${psql[@]}" -f "$SQLDIR/dev-fixture.sql"
    fi
fi
