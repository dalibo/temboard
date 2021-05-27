#!/bin/bash -eux

top_srcdir=$(readlink -m "$0/../../..")
cd "$top_srcdir"
test -f setup.py


DIST="$(rpm --eval %dist)"
if [ "${DIST}" = ".el8" ] ; then
	PYTHON=python3
else
	PYTHON=python2
fi


#       S O U R C E S
#
# Determine version to build, default to current checkout version.
if [ -z "${VERSION-}" ] ; then
	VERSION=$("$PYTHON" setup.py --version)
fi

# Ensure source tarball. If missing, try download from PyPI.
tarball=temboard-${VERSION}.tar.gz
if ! [ -f "dist/${tarball}" ] ; then
	mkdir -p dist
	(cd dist/; curl -LO "https://pypi.debian.net/temboard/${tarball}")
	test -f "dist/${tarball}"
fi

topdir=~testuser/rpmbuild
mkdir -p "$topdir/SOURCES" "$topdir/SPECS"
cp -vf packaging/rpm/temboard.spec "$topdir/SPECS/"
cp -vf "dist/$tarball" "$topdir/SOURCES/"
# rpmbuild requires files to be owned by running uid
chown -R testuser "$topdir"


#       B U I L D

# Disable PGDG repos, they eat network bandwith for nothing.
sed -i s/enabled=1/enabled=0/ /etc/yum.repos.d/pgdg-redhat-all.repo
yum-builddep -y packaging/rpm/temboard.spec

sudo -u testuser rpmbuild \
    --clean \
    --define "pkgversion ${VERSION}" \
    --define "_topdir $topdir" \
    -bb "$topdir/SPECS/temboard.spec"

# Pin rpm as latest built, for upload.
rpm=$(ls "$topdir/RPMS/noarch/temboard-${VERSION}"-*"${DIST}"*.rpm)
test -f "$rpm"
cp "$rpm" dist/
rpm="$(basename "$rpm")"
ln -fs "$rpm" dist/temboard-last.rpm
chown --no-dereference "$(stat -c %u:%g "dist/$tarball")" "dist/$rpm" dist/temboard-last.rpm


#       P E N   T E S T

yum install -y dist/temboard-last.rpm
rpm -q --list --changelog "temboard-${VERSION}"
(
	cd /
	temboard --version
	"$PYTHON" -c 'import temboardui.toolkit'
)
