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

systemctl restart --state=active temboard-agent@*
