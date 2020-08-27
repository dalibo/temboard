#!/bin/bash -eux

#
# Script to run tests on CentOS
#

top_srcdir=$(readlink -m $0/../../..)
cd $top_srcdir
# Ensure that setup.py exists (we are correctly located)
test -f setup.py

teardown() {
    exit_code=$?

    # If not on CI and we are docker entrypoint (PID 1), let's wait forever on
    # error. This allows user to enter the container and debug after a build
    # failure.
    if [ -z "${CI-}" -a $PPID = 1 -a $exit_code -gt 0 ] ; then
        tail -f /dev/null
    fi
}

trap teardown EXIT INT TERM

install_rpm=${TBD_INSTALL_RPM:-0}

# For circle-ci tests we want to install using RPM
# When launched locally we install via pip
if (( install_rpm == 1 ))
then
    # Search for the proper RPM package
    rpmdist=$(rpm --eval '%dist')
    rpm=$(readlink -e dist/rpm/noarch/temboard-agent-*${rpmdist}*.noarch.rpm)
    # Disable pgdg to use base pyscopg2 2.5 from Red Hat.
    yum -d1 "--disablerepo=pgdg*"  install -y $rpm
    rpm --query --queryformat= temboard-agent
else
    pip2 install -e .
    if type -p yum ; then
	    yum -q -y "--disablerepo=pgdg*" install python-psycopg2
    else
	    pip2 install psycopg2-binary
    fi
fi

pip2 install pytest

export LC_ALL=en_US.utf8
export TBD_PGBIN=$(readlink -e /usr/pgsql-${TBD_PGVERSION}/bin /usr/lib/postgresql/${TBD_PGVERSION}/bin)

# Remove any .pyc file to avoid errors with pytest and cache
find . -name \*.pyc -delete
rm -rf /tmp/tests_temboard
make -C tests/func/ pytest PYTEST_ARGS="${PYTEST_ARGS-$*}"
