#!/bin/bash -eux

#
# Script to run tests on CentOS
#

TOP_SRCDIR=$(readlink -m "$0/../../..")
cd "$TOP_SRCDIR"
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

# For circle-ci tests we want to install using RPM
# When launched locally we install via pip
if [ "${TBD_INSTALL_PKG-0}" = "1" ]
then
	if type -p yum &>/dev/null ; then
		# Search for the proper RPM package
		rpmdist=$(rpm --eval '%dist')
		rpm=$(readlink -e dist/temboard-agent-*${rpmdist}*.noarch.rpm)
		# Disable pgdg to use base pyscopg2 from EPEL.
		$(type -p retry) yum -d1 "--disablerepo=pgdg*"  install -y "$rpm"
		rpm --query --queryformat= temboard-agent
	elif type -p apt-get &>/dev/null ; then
		codename="$(grep -Po 'VERSION_CODENAME=\K.+' /etc/os-release)"
		deb="$(readlink -e dist/temboard-agent_*-"0dlb1${codename}1_all.deb")"
		apt-get update --quiet
		apt-get install --yes "$deb"
	fi
else
    python3 -m pip install -e .
    # Fake easy_install.pth dropped by new setuptools.
    echo "$PWD" > "$(python3 -c "import sys; print(sys.path[-1]);")/temboard-develop.pth"
    python3 -m pip install --only-binary :all: psycopg2-binary
fi

python3 -m pip install pytest pytest-mock

# Rockylinux 8 container has a bad locale configured. Configure locale
# according to system availabilities. This is important for initdb.
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
	python3 -m pytest \
	-vv --capture=no -p no:cacheprovider \
	"${@:-tests/func/}"
