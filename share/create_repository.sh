#!/bin/bash -eu

SQLDIR=$(readlink -m $0/../sql/)

export PGHOST=${PGHOST-/var/run/postgresql}
export PGDATABASE=${PGDATABASE-temboard}
TEMBOARD_PASSWORD=${TEMBOARD_PASSWORD-temboard}

if ! psql -d postgres -c "SELECT 'SKIP' FROM pg_catalog.pg_user WHERE usename = 'temboard'" | grep -q SKIP ; then
    psql -ad postgres -awc "CREATE ROLE temboard LOGIN PASSWORD '${TEMBOARD_PASSWORD}';"
fi

if ! psql -d postgres -c "SELECT 'SKIP' FROM pg_catalog.pg_database WHERE datname = 'temboard'" | grep -q SKIP ; then
    psql -ad postgres -awc "CREATE DATABASE temboard OWNER temboard;"
fi

if ! temboard-migratedb check ; then
    temboard-migratedb upgrade
    psql="psql -aw --set ON_ERROR_STOP=on --pset pager=off"
    if [ -n "${DEV-}" ] ; then
        $psql -f $SQLDIR/dev-fixture.sql
    fi
fi
