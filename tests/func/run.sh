#!/bin/bash -eux

top_srcdir=$(readlink -m $0/../../..)
cd $top_srcdir

LOGFILE=temboard-func.log
PIDFILE=$(readlink -m temboard-func.pid)

retrykill() {
	local pid=$1
	for i in {0..10} ; do
		if ! kill -0 $pid &>/dev/null; then
			return 0
		elif ps --no-headers -o state $pid | grep -q Z ; then
			: $pid is zombie
			return 0
		else
			kill $pid
			sleep $i
		fi
	done
	return 1
}

teardown() {
	exit_code=$?
	trap - EXIT INT TERM

	if [ -f $LOGFILE ] ; then
		# Trim line from syslog-like prefix.
		sed 's/.*\]: //g' $LOGFILE >&2
	fi

	# If not on CI and we are docker entrypoint (PID 1), let's wait forever on
	# error. This allows user to enter the container and debug after a build
	# failure.
	if [ -z "${CI-}" -a $PPID = 1 -a $exit_code -gt 0 ] ; then
		tail -f /dev/null
	fi

	if [ -f ${PIDFILE} ] ; then
		read pid < ${PIDFILE}
		retrykill $pid
		rm -f ${PIDFILE}
	fi
}
trap teardown EXIT INT TERM

install_ui_py() {
	mkdir -p ${XDG_CACHE_HOME-~/.cache}
	chown -R $(id -u) ${XDG_CACHE_HOME-~/.cache}
	rm -f /tmp/temboard-*.tar.gz
	python2 setup.py sdist --dist-dir /tmp
	pip3 install \
		--progress-bar off \
		--prefix=/usr/local --ignore-installed --upgrade \
		/tmp/temboard-*.tar.gz \
		psycopg2-binary
	wait-for-it.sh ${PGHOST}:5432
	if ! /usr/local/share/temboard/auto_configure.sh ; then
		cat /var/log/temboard-auto-configure.log >&2
		return 1
	fi
	mkdir -p /etc/temboard/temboard.conf.d
	cat >> /etc/temboard/temboard.conf.d/func-plugins.conf <<-EOF
	[temboard]
	plugins = ["dashboard", "pgconf", "activity", "monitoring", "maintenance", "extsample", "statements"]

	[sample]
	option = configured
	EOF
}

rm -f $LOGFILE
mkdir -p tests/func/home

if [ -n "${SETUP-1}" ] ; then
	install_ui_py
	pip3 install \
		--progress-bar off \
		--ignore-installed \
		--prefix=/usr/local \
		--upgrade \
		--requirement tests/func/requirements.txt \
		"$top_srcdir/tests/func/sample-plugin"
fi

if [ -n "${MANUAL-}" -a $PPID = 1 ] ; then
	exec tail -f /dev/null
fi

TEMBOARD_HOME=tests/func/home TEMBOARD_LOGGING_METHOD=file TEMBOARD_LOGGING_DESTINATION=${PWD}/$LOGFILE \
		       temboard --daemon --debug --pid-file ${PIDFILE}
UI=${UI-https://0.0.0.0:8888}
wait-for-it.sh ${UI#https://}

pytest \
	--base-url ${UI} \
	"$@" \
	tests/func/
