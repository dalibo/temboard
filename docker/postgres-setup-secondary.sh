# -*- mode: sh; sh-shell: bash -*-

set -x

pg_ctl stop
rm -rf "${PGDATA:?}"/*

for _ in {0..5} ; do
	if psql -h "$PRIMARY_HOST" ; then
		break
	else
		sleep 1
	fi
done

PGPASSWORD=gobelet pg_basebackup \
	-h "$PRIMARY_HOST" -p 5432 -U secondary \
	-D "$PGDATA" \
	--format=p \
	--write-recovery-conf \
	--wal-method=stream \
	--checkpoint=fast \
	--progress

pg_ctl start

set +x
