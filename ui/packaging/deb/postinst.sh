#!/bin/bash -eu

error() {
	echo -e "\e[1;31m$*\e[0m" >&2
}

if systemctl is-active temboard >&/dev/null ; then
	systemctl restart temboard
fi
