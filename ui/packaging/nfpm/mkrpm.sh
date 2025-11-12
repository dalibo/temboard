#!/bin/bash -eux
# use CLEAN=0 to avoid the final teardown tidoudou dou

TOP_SRCDIR=$(readlink -m "$0/../../..")
UID_GID=$(stat -c %u:%g "$0")
cd "$TOP_SRCDIR"
test -f setup.py

BUILDDIR=$(readlink -m packaging/nfpm/build)
DESTDIR=$BUILDDIR/destdir

teardown () {
    set +x
    if [ "0" = "${CLEAN-1}" ] ; then
        return
    fi

    rm -rf "$BUILDDIR"

    set -x
}
trap teardown EXIT INT TERM
CLEAN=1 teardown

mkdir -p "$DESTDIR"

#       V E R S I O N S

if [ -z "${VERSION-}" ] ; then
	VERSION=$(python3 setup.py --version)
fi
RELEASE="1$(rpm --eval '%{dist}')"

#       I N S T A L L

whl="dist/temboard-$VERSION-py3-none-any.whl"
if ! [ -f "$whl" ] ; then
	pip download --only-binary :all: --no-deps --pre --dest "dist/" "temboard==$VERSION"
fi

# Install from sources
pip3 install --pre --root "$DESTDIR" --prefix /usr --no-deps "$whl"
# Vendor dependencies.
pythonv=$(python3 --version |& grep -Po 'Python \K(3\.[0-9]{1,2})')
pip3 install \
	--pre --no-deps --requirement "$DESTDIR/usr/share/temboard/vendor.txt" \
	--target "$DESTDIR/usr/lib/python$pythonv/site-packages/temboardui/_vendor"

#       B U I L D

pythonbin="$(type -p "python$pythonv")"
PYTHONPKG="$(rpm -qf "$pythonbin")"
PYTHONPKG="${PYTHONPKG%%-*}"

(
	export VERSION
	export RELEASE
	export PYTHONPKG
	nfpm pkg --config packaging/nfpm/nfpm.yaml --packager rpm
)

#       T E S T

rpm="temboard-${VERSION}-${RELEASE}.noarch.rpm"
mv "$rpm" dist/
rpm -qpl "dist/$rpm"
yum -q -y --disablerepo='pgdg*' install "dist/$rpm"
(
	cd /
	temboard --version
	test -f /usr/lib/python*/site-packages/temboardui/static/dist/.vite/manifest.json
	test -x /usr/share/temboard/auto_configure.sh
	test -f /usr/lib/systemd/system/temboard.service
)
