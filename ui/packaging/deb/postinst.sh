#!/bin/bash -eu

error() {
	echo -e "\e[1;31m$*\e[0m" >&2
}

if systemctl is-active temboard >&/dev/null ; then
	systemctl restart temboard
elif ! [ -f /etc/temboard/temboard.conf ] && [ -x /usr/share/temboard/auto_configure.sh ] ; then
	if ! /usr/share/temboard/auto_configure.sh ; then
		error "Auto-configuration failed. Skipping."
		error "See documentation for how to setup."
	fi
fi
