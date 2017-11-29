#!/bin/bash -eux

cd $(readlink -m $0/../..)
test -f setup.py

teardown() {
    exit_code=$?
    chown --recursive $(stat -c %u:%g setup.py) rpm/ $(readlink -e build/) $(readlink -e dist/)
    trap - EXIT

    # If not on CI and we are docker entrypoint (PID 1), let's wait forever on
    # error. This allows user to enter the container and debug after a build
    # failure.
    if [ -z "${CI-}" -a $$ = 1 -a $exit_code -gt 0 ] ; then
        tail -f /dev/null
    fi
}

yum_install() {
    local packages=$*
    yum install -y $packages
    rpm --query --queryformat= $packages
}

trap teardown EXIT INT TERM

yum_install epel-release
yum_install python-setuptools rpm-build

# Building sources in rpm/
python setup.py sdist --dist-dir rpm/
! diff -u \
  --label ../share/temboard-agent.conf share/temboard-agent.conf \
  rpm/temboard-agent.rpm.conf > rpm/temboard-agent.conf.patch

# rpmbuild requires files to be owned by running uid
chown --changes --recursive $(id -u):$(id -g) rpm/

rpmbuild \
    --define "pkgversion $(python setup.py --version)" \
    --define "_topdir ${PWD}/dist/rpm" \
    --define "_sourcedir ${PWD}/rpm" \
    -ba rpm/temboard-agent.spec
