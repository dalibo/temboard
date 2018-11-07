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

# Find source tarball
if [ -z "${VERSION-}" ] ; then
	# Find latest published version.
	VERSION=$(curl https://pypi.debian.net/temboard-agent/ | grep -Po '>temboard-agent-\K.*(?=\.tar\.gz)' | tail -1)
fi
tarball=temboard-agent-${VERSION}.tar.gz
if ! [ -f dist/${tarball} ] ; then
	# Fetch missing tarball.
	mkdir -p dist
	(cd dist/; curl -LO https://pypi.debian.net/temboard-agent/${tarball} )
	test -f dist/${tarball}
fi
ln -f dist/${tarball} packaging/rpm/

# rpmbuild requires files to be owned by running uid
sudo chown --recursive $(id -u):$(id -g) packaging/rpm/

rpmbuild \
    --define "pkgversion ${VERSION}" \
    --define "_topdir ${PWD}/dist/rpm" \
    --define "_sourcedir ${PWD}/packaging/rpm" \
    -bb packaging/rpm/temboard-agent.spec

# Pin rpm as latest built, for upload.
rpm=$(ls dist/rpm/noarch/temboard-agent-${VERSION}-*${DIST}*.noarch.rpm)
ln -fs $(basename $rpm) dist/rpm/noarch/last_build.rpm

# Test it
if [ "${DIST}" = "el6" ] ; then
    sudo yum install -y epel-release
fi

sudo yum install -y $rpm
temboard-agent --help
