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
# switchover with dev/bin/switchover.sh script which will promote the secondary.
#
# If a postgres is down, restart it manually with docker compose.
# If you need to reset the setup, trash with make clean.

# shellcheck source=/dev/null
. /usr/local/bin/docker-entrypoint.sh

_ha_setup() {
    docker_setup_env

    chown postgres:postgres /var/lib/postgresql/archive

    echo "Waiting for $PEER_HOST to have network."
    if ! peerhost="$(_retry getent hosts "$PEER_HOST")"; then
        echo "$PEER_HOST down. Can't elect primary."
        exit 1
    fi

    if [ "$DATABASE_ALREADY_EXISTS" = "true" ]; then
        # We are in restarting mode.
        # Check if the other node is primary.
        # Or guess based on IP.
        if is_in_recovery=$(_retry env PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$PEER_HOST" -U "$POSTGRES_USER" -Aqt -c 'SELECT pg_is_in_recovery();'); then
            if [ "$is_in_recovery" = "t" ]; then
                echo "$PEER_HOST restarted as secondary. Restarting as primary."
                rm -f "$PGDATA/standby.signal"
            else
                echo "$PEER_HOST restarted as primary. Failback as secondary."
                _ha_failback
            fi
        else
            # If other node does not respond he may be waiting for us too.
            # To release this deadlock, fallback to initial election base on _ha_have_i_precedence.
            if _ha_have_i_precedence "$peerhost"; then
                echo "$PEER_HOST does not respond. Restarting as primary from precedence."
                # Offline pg_promote()
                rm -f "$PGDATA/standby.signal"
            else
                echo "$PEER_HOST does not respond. Restarting as secondary from precedence."
                _ha_failback
            fi
        fi
    else
        if _ha_have_i_precedence "$peerhost"; then
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

_ha_have_i_precedence() {
    # Compute precedence based on IP.
    IFS=" " read -r _ winner _ < <((
        getent hosts "$HOSTNAME"
        echo "$1"
    ) | sort | head -1)
    echo "$winner has precedence."
    test "${winner}" = "$HOSTNAME"
}

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

_ha_failback() {
    # offline pg_demote.
    touch "$PGDATA/standby.signal"
    echo "Waiting for primary to come up."
    _retry env PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$PEER_HOST" -U "$POSTGRES_USER" -Aqt -c "SELECT pg_switch_wal();"
    echo "Rewind pgdata to failback."
    gosu postgres pg_rewind \
        --source-server="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$PEER_HOST:5432/" \
        --target-pgdata="$PGDATA" \
        --write-recovery-conf \
        --no-ensure-shutdown
}

_retry() {
    for i in {2..7}; do
        if "$@"; then
            return
        else
            echo "Retrying in one second, attempt #$i."
            sleep 1
        fi
    done

    "$@"
}

if [ -v PEER_HOST ]; then
    PGAPP="dev-docker-ha-entrypoint" _ha_setup
else
    echo 'PEER_HOST undefined. No HA setup.'
fi

# trigger docker-entrypoin.sh main
_main "$@"
