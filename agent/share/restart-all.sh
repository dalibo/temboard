#!/bin/bash -eu

if ! hash systemctl &>/dev/null; then
	echo You must restart manually temboard-agent services. >&2
	exit 0
fi

if ! systemctl is-system-running &>/dev/null ; then
	echo You must restart manually temboard-agent services. >&2
	exit 0
fi

systemctl daemon-reload

prefix=temboard-agent@
active_units="$(systemctl --plain list-units ${prefix}* | grep -Po ${prefix}.*\\.service ||:)"

if [ -z "${active_units}" ] ; then
	echo No units found for temboard-agent. >&2
	exit 0;
fi

exit_code=0
for unit in ${active_units} ; do
	echo Restarting $unit >&2
	if ! systemctl restart $unit ; then
		echo Failed to restart $unit >&2
		exit_code=1
	fi
done

exit $exit_code
