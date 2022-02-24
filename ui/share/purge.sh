#!/bin/bash -eu
#
# purge.sh purges all temboard files and configuration, except database.

ETCDIR=${ETCDIR-/etc/temboard}
VARDIR=${VARDIR-/var/lib/temboard}
LOGDIR=${LOGDIR-/var/log/temboard}
LOGFILE=${LOGFILE-/var/log/temboard-purge.log}

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

if [ -n "${DEBUG-}" ] ; then
	exec 3>/dev/null
else
	exec 3>&2 2>"${LOGFILE}" 1>&2
	chmod 0600 "${LOGFILE}"
	trap 'catchall' INT EXIT TERM
fi

# Now, log everything.
set -x

if systemctl cat temboard &>/dev/null ; then
	systemctl disable --now temboard
	systemctl reset-failed temboard || true
fi

if getent passwd temboard ; then
	userdel temboard
fi

sudo -iu postgres dropdb --if-exists temboard
sudo -iu postgres dropuser --if-exists temboard

rm -rf "${ETCDIR}" "${VARDIR}" "${LOGDIR}"
