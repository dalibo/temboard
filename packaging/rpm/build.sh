#!/bin/bash -eux

cd $(readlink -m $0/../../..)
test -f setup.py

teardown() {
    exit_code=$?
    # rpmbuild requires files to be owned by running uid
    sudo chown --recursive $(id -u):$(id -g) packaging/rpm/

    trap - EXIT INT TERM

    # If not on CI and we are docker entrypoint (PID 1), let's wait forever on
    # error. This allows user to enter the container and debug after a build
    # failure.
    if [ -z "${CI-}" -a $$ = 1 -a $exit_code -gt 0 ] ; then
        tail -f /dev/null
    fi
}

trap teardown EXIT INT TERM

sudo yum-builddep -y packaging/rpm/temboard-agent.spec
sudo sed -i s/.centos// /etc/rpm/macros.dist

# Building sources in rpm/
python setup.py sdist --dist-dir packaging/rpm/
! diff -u \
  --label ../share/temboard-agent.conf \
  share/temboard-agent.conf packaging/rpm/temboard-agent.rpm.conf \
  > packaging/rpm/temboard-agent.conf.patch

# rpmbuild requires files to be owned by running uid
sudo chown --recursive $(id -u):$(id -g) packaging/rpm/

rpmbuild \
    --define "pkgversion $(python setup.py --version)" \
    --define "_topdir ${PWD}/dist/rpm" \
    --define "_sourcedir ${PWD}/packaging/rpm" \
    -ba packaging/rpm/temboard-agent.spec

# Test it
if [ "${DIST}" = "el6" ] ; then
    sudo yum install -y epel-release
fi

sudo yum install -y dist/rpm/noarch/temboard-agent-*${DIST}*.noarch.rpm
temboard-agent --help
