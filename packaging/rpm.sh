#!/bin/bash -eux

cd $(readlink -m $0/../..)
test -f setup.py

teardown() {
    chown --recursive $(stat -c %u:%g setup.py) packaging/ $(readlink -e build/ dist/)
    trap - EXIT

    # Ease debugging from Docker container by waiting for explicit shutdown.
    if [ -z "${CI-}" ] && ! test -t 0 ; then
        tail -f /dev/null
    fi
}

yum_install() {
    local packages=$*
    yum install -y $packages
    rpm --query --queryformat= $packages
}

trap teardown EXIT INT TERM

yum_install epel-release rpm-build
yum-builddep -y packaging/temboard.spec

# Building sources in packaging/
python setup.py sdist --dist-dir packaging/
! diff -u \
  --label ../share/temboard.conf share/temboard.conf \
  rpm/temboard.conf > packaging/temboard.conf.patch

# rpmbuild requires files to be owned by running uid
chown --changes --recursive $(id -u):$(id -g) packaging/

version=$(python setup.py --version)
rpmbuild \
    --define "pkgversion $version" \
    --define "_topdir ${PWD}/dist/" \
    --define "_sourcedir ${PWD}/packaging/" \
    -ba packaging/temboard.spec

# Pen test
yum install -y dist/RPMS/noarch/temboard-${version}-*.noarch.rpm
temboard --help
