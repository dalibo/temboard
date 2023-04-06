#!/bin/bash -eux
#
# Switch over replication of development instances postgres0 and postgres1.
#
# Tested with postgres-14
#

_psql()
{
	# Usage: psql SERVICE COMMAND [ARGS...]
	local num=${1#postgres}; shift
	PGUSER=postgres PGPASSWORD=postgres PGHOST=0.0.0.0 PGPORT=$((1+num))5432 PGDATABASE=postgres psql -AqtX "$@"
}


# Guess topology
for server in postgres0 postgres1 ; do
	if ! replications="$(_psql $server -c 'SELECT * FROM pg_stat_replication;')" ; then
		: "Is $server down ?. restart it before running this script."
		exit 1
	fi

	mapfile -t replications < <(echo -n "$replications")

	case "${#replications[@]}" in
		0)
			secondary=$server
			;;
		1)
			primary=$server
			;;
		*)
			: "Unhandled replication state. Please advise."
			exit 1
			;;
	esac
done

docker-compose stop $primary
_psql $secondary -c 'SELECT pg_promote();'
# Swap variables
servers=("$secondary" "$primary")
primary="${servers[0]}"
secondary="${servers[1]}"
# failback. The entrypoint takes care of rebuilding the data with pg_rewind.
docker-compose up -d "$secondary"

sleep 3

# Check primary has a replication client.
_psql "$primary" -c "SELECT * FROM pg_stat_replication;" | grep "$secondary"
# Check secondary is in recovery.
_psql "$secondary" -c "SELECT pg_is_in_recovery();" | grep t

: Primary is $primary
: Secondary is $secondary
