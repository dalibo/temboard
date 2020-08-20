#!/bin/bash -eu

if [ -n "${DEBUG-}" ] ; then
	set -x
fi

ETCDIR=${ETCDIR-/etc/temboard-agent}
VARDIR=${VARDIR-/var/lib/temboard-agent}
LOGDIR=${LOGDIR-/var/log/temboard-agent}

instance_path="$1"
instance_name="${instance_path//\//-}"

if type -p systemctl >/dev/null ; then
	echo "Stopping and disabling systemd service." >&2
	! systemctl disable --now "temboard-agent@$instance_name"
fi

echo "Cleaning files and directories..." >&2
rm -rvf \
	"${ETCDIR:?}/$instance_path/" \
	"${LOGDIR:?}/$instance_path.log" \
	"${VARDIR:?}/$instance_path/" \
	"/etc/systemd/system/temboard-agent@${instance_path}.service.d" \
;

echo "temBoard agent ${instance_name} stopped and cleaned." >&2
