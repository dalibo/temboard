#!/bin/bash -eux

cd $(readlink -m $0/../../..)
test -f setup.py

teardown() {
	exit_code=$?
	set +x;
	# rpmbuild requires files to be owned by running uid
	sudo chown --recursive $(id -u):$(id -g) packaging/rpm/
	rm -f packaging/rpm/temboard*.tar.gz

	trap - EXIT INT TERM

	# If not on CI and we are docker entrypoint (PID 1), let's wait forever
	# on error. This allows user to enter the container and debug after a
	# build failure.
	if [ -z "${CI-}" -a $$ = 1 -a $exit_code -gt 0 ] ; then
		echo "Waiting forever. Debug with" >&2
		echo "	docker exec -it $(hostname) /bin/bash"
		tail -f /dev/null
	fi
}

trap teardown EXIT INT TERM

sudo yum-builddep -y packaging/rpm/temboard.spec
sudo sed -i s/.centos// /etc/rpm/macros.dist

# Find source tarball
if [ -z "${VERSION-}" ] ; then
	# Find latest published version.
	VERSION=$(curl -s https://pypi.debian.net/temboard/ | grep -Po '>temboard-\K.*(?=\.tar\.gz)' | tail -1)
fi
tarball=temboard-${VERSION}.tar.gz
if ! [ -f dist/${tarball} ] ; then
	# Fetch missing tarball.
	mkdir -p dist
	(cd dist/; curl -LO https://pypi.debian.net/temboard/${tarball} )
	test -f dist/${tarball}
fi
ln -f dist/${tarball} packaging/rpm/

# rpmbuild requires files to be owned by running uid
sudo chown --recursive $(id -u):$(id -g) packaging/rpm/

rpmbuild \
	--clean \
	--define "pkgversion ${VERSION}" \
	--define "_topdir ${PWD}/dist/rpm" \
	--define "_sourcedir ${PWD}/packaging/rpm" \
	-bb packaging/rpm/temboard.spec

# Pin RPM as latest built, for upload.
rpm=$(ls dist/rpm/noarch/temboard-${VERSION}-*${DIST}*.noarch.rpm)
ln -fs $(basename $rpm) dist/rpm/noarch/last_build.rpm

# Test it
sudo yum install -y epel-release  # for alembic
sudo yum install -y $rpm
(
	cd /;
	temboard --version;
	python3 -c 'import temboardui.toolkit';

)
