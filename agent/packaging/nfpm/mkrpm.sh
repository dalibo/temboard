#!/bin/bash -eux
# use CLEAN=0 to avoid the final teardown tidoudou dou

TOP_SRCDIR=$(readlink -m "$0/../../..")
UID_GID=$(stat -c %u:%g "$0")
cd "$TOP_SRCDIR"
test -f temboardagent/__init__.py

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

mapfile -t pythons < <(compgen -c python3. | grep -v config | sort --reverse --unique --version-sort)
python="${pythons[0]}"
pip=("$python" -m pip)

if [ -z "${VERSION-}" ] ; then
	VERSION=$(uv version --short)
fi
RELEASE="1$(rpm --eval '%{dist}')"

#       I N S T A L L


whl="dist/temboard_agent-$VERSION-py3-none-any.whl"
if ! [ -f "$whl" ] ; then
	"${pip[@]}" download --only-binary :all: --no-deps --pre --dest "dist/" "temboard-agent==$VERSION"
fi

# Install from sources
"${pip[@]}" install --pre --root "$DESTDIR" --prefix /usr --no-deps "$whl"
# Vendor dependencies.
pythonv=$("$python" --version |& grep -Po 'Python \K(3\.[0-9]{1,2})')
"${pip[@]}" install \
	--pre --no-deps --requirement "$TOP_SRCDIR/vendor.txt" \
	--target "$DESTDIR/usr/lib/python$pythonv/site-packages/temboardagent/_vendor"

#       B U I L D

pythonbin="$(type -p "$python")"
PYTHONPKG="$(rpm -qf "$pythonbin")"
PYTHONPKG="${PYTHONPKG%%-*}"

(
	export VERSION
	export RELEASE
	export PYTHONPKG
	nfpm pkg --config packaging/nfpm/nfpm.yaml --packager rpm
)

#       T E S T

rpm="temboard-agent-${VERSION}-${RELEASE}.noarch.rpm"
mv "$rpm" dist/
rpm -qpl "dist/$rpm"
yum -q -y --disablerepo='extras*' --disablerepo='pgdg*' --disablerepo='epel*' --disablerepo='powertools*' install "dist/$rpm"
(
	cd /
	temboard-agent --version
)
