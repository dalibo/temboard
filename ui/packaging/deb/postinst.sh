#!/bin/bash -eu

if ! readlink /proc/1/exe | grep -q systemd ; then
	echo You must restart manually temboard service. >&2
	exit 0
fi

systemctl daemon-reload

# Restart if running.
systemctl try-restart temboard
