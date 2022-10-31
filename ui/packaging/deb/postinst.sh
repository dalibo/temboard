#!/bin/bash -eu

if systemctl daemon-reload &>/dev/null ; then
	systemctl restart --state=ACTIVE temboard
fi
