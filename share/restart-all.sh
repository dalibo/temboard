#!/bin/bash -eu

if ! hash systemctl &>/dev/null; then
	echo You must restart manually temboard-agent services. >&2
	exit 0
fi

prefix=temboard-agent@
units="$(systemctl --plain list-units ${prefix}* | grep -Po ${prefix}.*\\.service)"

if [ -z "${units}" ] ; then
	echo No units found for temboard-agent.
fi

exit_code=0
for unit in ${units} ; do
	echo Restarting $unit >&2
	if ! systemctl restart $unit ; then
		echo Failed to restart $unit >&2
		exit_code=1
	fi
done

exit $exit_code
