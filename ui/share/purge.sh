#!/bin/bash -eu
#
# purge.sh purges all temboard files and configuration, except database.

ETCDIR=${ETCDIR-/etc/temboard}
VARDIR=${VARDIR-/var/lib/temboard}
LOGDIR=${LOGDIR-/var/log/temboard}
LOGFILE=${LOGFILE-/var/log/temboard-purge.log}
SYSUSER=${SYSUSER-temboard}

catchall() {
	# shellcheck disable=SC2181
	if [ $? -gt 0 ] ; then
		fatal "Failure. See ${LOGFILE} for details."
	else
		rm -f "${LOGFILE}"
	fi
	trap - INT EXIT TERM
}

fatal() {
	echo -e "\\e[1;31m$*\\e[0m" | tee -a /dev/fd/3 >&2
	exit 1
}

log() {
	echo "$@" | tee -a /dev/fd/3 >&2
}

if [ -n "${DEBUG-}" ] ; then
	exec 3>/dev/null
else
	exec 3>&2 2>"${LOGFILE}" 1>&2
	chmod 0600 "${LOGFILE}"
	trap 'catchall' INT EXIT TERM
fi

# Now, log everything.
set -x

if systemctl is-system-running && systemctl cat temboard &>/dev/null ; then
	systemctl disable --now temboard
	systemctl reset-failed temboard || true
fi

if getent passwd "$SYSUSER" && [ "$(whoami)" != "$SYSUSER" ]; then
	userdel "$SYSUSER"
fi

if [ -d "$PGHOST" ] ; then
	# If local, sudo to PGUSER.
	run_as_postgres=(sudo -nEHu "${PGUSER}")
else
	run_as_postgres=(env)
fi

"${run_as_postgres[@]}" dropdb --if-exists "${TEMBOARD_DATABASE-temboard}"
"${run_as_postgres[@]}" dropuser --if-exists temboard || :

rm -rf "${ETCDIR}" "${VARDIR}" "${LOGDIR}" "/etc/pki/tls/*/temboard-auto.*"

log "temBoard UI unconfigured."
