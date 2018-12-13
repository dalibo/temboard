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
		cat $LOGFILE >&2
	fi

	# If not on CI and we are docker entrypoint (PID 1), let's wait forever on
	# error. This allows user to enter the container and debug after a build
	# failure.
	if [ -z "${CI-}" -a $$ = 1 -a $exit_code -gt 0 ] ; then
		tail -f /dev/null
	fi

	if [ -f ${PIDFILE} ] ; then
		read pid < ${PIDFILE}
		retrykill $pid
		rm -f ${PIDFILE}
	fi
}
trap teardown EXIT INT TERM

# For CentOS
export PYTHONPATH=/usr/local/python2.7/lib/site-packages

install_ui_py() {
	mkdir -p ${XDG_CACHE_HOME-~/.cache}
	chown -R $(id -u) ${XDG_CACHE_HOME-~/.cache}
	pip2.7 install --ignore-installed --prefix=/usr/local --upgrade .
	wait-for-it.sh ${PGHOST}:5432
	if ! /usr/local/share/temboard/auto_configure.sh ; then
		cat /var/log/temboard-auto-configure.log >&2
	fi
}

install_ui_py
pip2.7 install \
       --ignore-installed \
       --prefix=/usr/local \
       --upgrade \
       --requirement tests/func/requirements.txt

rm -f $LOGFILE
TEMBOARD_LOGGING_METHOD=file TEMBOARD_LOGGING_DESTINATION=$LOGFILE \
		       temboard --daemon --debug --pid-file ${PIDFILE}
wait-for-it.sh 0.0.0.0:8888

pytest \
	--driver Remote \
	--host ${SELENIUM-selenium} \
	--capability browserName firefox \
	--base-url https://ui:8888 \
	"$@" \
	tests/func/
