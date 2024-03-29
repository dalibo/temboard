#!/bin/bash -eux

top_srcdir=$(readlink -m "$0/../../..")
cd "$top_srcdir"
test -f setup.py
if [ -z "${VERSION-}" ] ; then
	VERSION=$(grep -Po '__version__ = "\K[^"]+' temboardui/version.py)
fi
test -f "dist/temboard-$VERSION.tar.gz"
cp --preserve --force packaging/rpm/temboard.spec /tmp/temboard.spec
sed -i "/^Version:/s/GENERATED/$VERSION/" /tmp/temboard.spec
export BUILDDIR="$PWD/dist/" SMOKETEST=1
exec rpmbuild.sh /tmp/temboard.spec "dist/temboard-$VERSION.tar.gz"
