#!/bin/bash -eux

top_srcdir=$(readlink -m "$0/../../..")
cd "$top_srcdir"
test -f setup.py


#       S O U R C E S

# Determine version to build, default to current checkout version.
if [ -z "${VERSION-}" ] ; then
	VERSION=$(python3 setup.py --version)
fi

# Ensure source tarball. If missing, try download from PyPI.
tarball=temboard-agent-${VERSION}.tar.gz
if ! [ -f "dist/${tarball}" ] ; then
	mkdir -p dist
	(cd dist/; curl -LO "https://pypi.debian.net/temboard-agent/${tarball}")
	test -f "dist/${tarball}"
fi

topdir=~testuser/rpmbuild
mkdir -p "$topdir/SOURCES" "$topdir/SPECS"
cp -vf packaging/rpm/temboard-agent.spec "$topdir/SPECS/"
cp -vf \
	"dist/$tarball" \
	packaging/rpm/temboard-agent.init \
	packaging/rpm/temboard-agent.rpm.conf \
	packaging/rpm/temboard-agent.service \
	"$topdir/SOURCES/"
# rpmbuild requires files to be owned by running uid
chown -R testuser "$topdir"


#       B U I L D

# Disable PGDG repos, they eat network bandwith for nothing.
sed -i s/enabled=1/enabled=0/ /etc/yum.repos.d/pgdg-redhat-all.repo
yum-builddep -y packaging/rpm/temboard-agent.spec

sudo -u testuser rpmbuild \
    --clean \
    --define "pkgversion ${VERSION}" \
    --define "_topdir $topdir" \
    -bb "$topdir/SPECS/temboard-agent.spec"

# Pin rpm as latest built, for upload.
DIST=$(rpm --eval %dist)
rpm=$(ls "$topdir/RPMS/noarch/temboard-agent-${VERSION}"-*"${DIST}"*.rpm)
test -f "$rpm"
cp "$rpm" dist/
rpm="$(basename "$rpm")"
ln -fs "$rpm" dist/temboard-agent-last.rpm
chown --no-dereference "$(stat -c %u:%g "dist/$tarball")" "dist/$rpm" dist/temboard-agent-last.rpm


#       P E N   T E S T

yum install -y dist/temboard-agent-last.rpm
rpm -q --list --changelog "temboard-agent-${VERSION}"
(
	cd /
	temboard-agent --version
	python3 -c 'import temboardagent.toolkit'
)
