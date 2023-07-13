#!/bin/bash -eu

if systemctl is-active temboard &>/dev/null ; then
	systemctl restart temboard
fi
