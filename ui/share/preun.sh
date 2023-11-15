#!/bin/bash
set -eu
mode="$1"

# rpm uses an int. deb uses a keyword.
case "$mode" in
	remove|0)
		if ! readlink /proc/1/exe | grep -q systemd ; then
			echo You must disable manually temboard service. >&2
			exit 0
		fi

		systemctl disable --now temboard
		if systemctl -q is-failed temboard ; then
			systemctl reset-failed temboard
		fi
		exit 0
		;;
	upgrade|1)
		exit 0
		;;
	*)
		echo "Unknown scriptlet execution mode: '$mode'. Skipping" >&2
		exit 0
		;;
esac
