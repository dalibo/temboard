#!/bin/bash -eux

top_srcdir=$(readlink -m "$0/../../..")
cd "$top_srcdir"
test -f setup.py
if [ -z "${VERSION-}" ] ; then
	VERSION=$(grep -Po '__version__ = "\K[^"]+' temboardagent/version.py)
fi
dist="dist/temboard-agent-$VERSION.tar.gz"
test -f "$dist"
cp --preserve --force packaging/rpm/temboard-agent.spec /tmp/temboard-agent.spec
sed -i "/^Version:/s/GENERATED/$VERSION/" /tmp/temboard-agent.spec
export BUILDDIR="$PWD/dist/"
exec rpmbuild.sh /tmp/temboard-agent.spec "$dist"
