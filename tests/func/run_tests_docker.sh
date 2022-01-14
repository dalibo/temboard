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
	set +x
	cat <<-EOF

                F A I L U R E

	This container will wait forever. To rexecute tests in this container,
	open a shell with 'make shell' and execute pytest with
	'run_tests_docker.sh'.

            $ make -C tests/func shell
            docker-compose exec test /bin/bash
            [root@b09dc2ff4a88 workspace]# ./tests/func/run_tests_docker.sh --pdb
            ...

	EOF
	echo -e '\e[33;1mTests failed. Hit Ctrl-C to terminate.\e[0m'

        tail -f /dev/null
    fi
}

trap teardown EXIT INT TERM

install_rpm=${TBD_INSTALL_RPM:-0}
PYTHON="$(type -p "${PYTHON-python3}")"

# For circle-ci tests we want to install using RPM
# When launched locally we install via pip
if (( install_rpm == 1 ))
then
    # Search for the proper RPM package
    rpmdist=$(rpm --eval '%dist')
    rpm=$(readlink -e dist/temboard-agent-*${rpmdist}*.noarch.rpm)
    # Disable pgdg to use base pyscopg2 2.5 from Red Hat.
    yum -d1 "--disablerepo=pgdg*"  install -y $rpm
    rpm --query --queryformat= temboard-agent
else
    $PYTHON -m pip install -e .
    # Fake easy_install.pth dropped by new setuptools.
    echo "$PWD" > "$("$PYTHON" -c "import sys; print(sys.path[-1]);")/temboard-develop.pth"
    if type -p yum &>/dev/null && $PYTHON --version | grep -F 'Python 2' ; then
	    yum -q -y "--disablerepo=pgdg*" install python-psycopg2
    else
	    $PYTHON -m pip install --only-binary :all: psycopg2-binary
    fi
fi

$PYTHON -m pip install pytest pytest-mock

# CentOS 8 container has a bad locale configured. Configure locale according to
# system availabilities. This is important for initdb.
for locale in en_US.utf8 en_US.UTF-8 C.utf8 C.UTF-8 ; do
	if locale -a | grep -q "$locale" ; then
		export LANG="$locale"
		break
	fi
done

export TBD_PGBIN=$(readlink -e /usr/pgsql-${TBD_PGVERSION}/bin /usr/lib/postgresql/${TBD_PGVERSION}/bin)
export TBD_WORKPATH="/tmp"

# Remove any .pyc file to avoid errors with pytest and cache
find . -name \*.pyc -delete
rm -rf /tmp/tests_temboard
temboard-agent --version
sudo -Eu testuser \
	/usr/bin/env PATH="$PATH" \
	"$PYTHON" -m pytest \
	-vv --capture=no -p no:cacheprovider \
	tests/func/ \
	"$@"
