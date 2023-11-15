#!/bin/bash
set -eu
mode="$1"

# rpm uses an int. deb uses a keyword.
case "$mode" in
	0|remove)
		if ! readlink /proc/1/exe | grep -q systemd ; then
			echo You must disable manually temboard-agent services. >&2
			exit 0
		fi

		while read -r service ; do
			systemctl disable --now "$service"
			if systemctl -q is-failed "$service" ; then
				systemctl reset-failed "$service"
			fi
		done < <(systemctl list-units --full --no-legend --no-pager --plain --type service temboard-agent@* | grep -Po '^[^.]+')
		exit 0
		;;
	1|upgrade)
		exit 0
		;;
	*)
		echo "Unknown scriptlet execution mode: '$mode'. Skipping" >&2
		exit 0
		;;
esac
