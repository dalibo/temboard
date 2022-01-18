#!/bin/bash -eux

top_srcdir=$(readlink -m $0/../../..)
cd $top_srcdir

LOGFILE="$PWD/temboard-func.log"
PIDFILE=$(readlink -m temboard-func.pid)
PYTHONBIN=${PYTHONBIN:-python3}

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

	if [ -f "${PIDFILE}" ] ; then
		read -r pid < "${PIDFILE}"
		# clean pidfile if temboard is dead.
		if ! kill -0 "$pid" ; then
			rm -f "$PIDFILE"
		fi
	fi


	# If not on CI and we are docker entrypoint (PID 1), let's wait forever on
	# error. This allows user to enter the container and debug after a build
	# failure.
	if [ -z "${CI-}" -a $PPID = 1 -a $exit_code -gt 0 ] ; then
		tail -f /dev/null
	fi

	if [ -n "${pid-}" ] ; then
		retrykill "$pid"
		rm -f "${PIDFILE}"
	fi
}
trap teardown EXIT INT TERM

install_ui_deb() {
	. /etc/os-release
	deb="$(readlink -e dist/temboard_*-"0dlb1${VERSION_CODENAME}1_amd64.deb")"
	test -f "$deb"
	apt update
	apt install "$deb"
	# Define extsample target installation directory
	PYTHONPREFIX=/usr/lib/temboard/
	# Use same interpreter as deb virtualenv
	python=(/usr/lib/temboard/lib/python*)
	PYTHONBIN="${python[0]##*/}"
}

install_ui_py() {
	mkdir -p ${XDG_CACHE_HOME-~/.cache}
	chown -R $(id -u) ${XDG_CACHE_HOME-~/.cache}
	rm -f /tmp/temboard-*.tar.gz
	$PYTHONBIN setup.py sdist --dist-dir /tmp
	$PYTHONBIN -m pip install \
		--prefix=/usr/local --ignore-installed --upgrade \
		/tmp/temboard-*.tar.gz \
		psycopg2-binary
}

install_ui_rpm() {
	rpmdist=$(rpm --eval '%dist')
	rpm=$(readlink -e dist/temboard-*"${rpmdist}"*.noarch.rpm)
	# Disable pgdg to use base pyscopg2 2.5 from Red Hat.
	yum -d1 "--disablerepo=pgdg*"  install -y "$rpm"
	rpm --query --queryformat= temboard
}

rm -f $LOGFILE
mkdir -p tests/func/home

if [ -n "${SETUP-1}" ] ; then
	if type -p yum &>/dev/null && [ "${TBD_INSTALL_RPM-}" = 1 ] ; then
		install_ui_rpm
	elif type -p apt &>/dev/null ; then
		install_ui_deb
	else
		install_ui_py
	fi

	temboard --version

	wait-for-it.sh ${PGHOST}:5432
	auto_configure="$(readlink -e /usr{/local,}/share/temboard/auto_configure.sh | head -1)"
	if ! "$auto_configure" ; then
		cat /var/log/temboard-auto-configure.log >&2
		exit 1
	fi

	$PYTHONBIN -m pip --version
	$PYTHONBIN -m pip install \
		--ignore-installed \
		--prefix="${PYTHONPREFIX-/usr/local}" \
		"$top_srcdir/tests/func/sample-plugin"

	$PYTHONBIN -m pip install \
		--ignore-installed \
		--upgrade \
		--requirement tests/func/requirements.txt

	mkdir -p /etc/temboard/temboard.conf.d
	cat >> /etc/temboard/temboard.conf.d/func-plugins.conf <<-EOF
	[temboard]
	plugins = ["dashboard", "pgconf", "activity", "monitoring", "maintenance", "extsample", "statements"]

	[sample]
	option = configured
	EOF
fi

if [ -n "${MANUAL-}" -a $PPID = 1 ] ; then
	exec tail -f /dev/null
fi

TEMBOARD_HOME=tests/func/home TEMBOARD_LOGGING_METHOD=file TEMBOARD_LOGGING_DESTINATION=$LOGFILE \
		       temboard --debug --daemon --pid-file ${PIDFILE}
UI=${UI-https://0.0.0.0:8888}
wait-for-it.sh ${UI#https://}

pytest \
	--base-url ${UI} \
	"$@" \
	tests/func/
