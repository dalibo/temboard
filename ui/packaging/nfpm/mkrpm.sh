#!/bin/bash -eux
# use CLEAN=0 to avoid the final teardown tidoudou dou

TOP_SRCDIR=$(readlink -m "$0/../../..")
UID_GID=$(stat -c %u:%g "$0")
cd "$TOP_SRCDIR"
test -f pyproject.toml

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

# Install from sources
"${pip[@]}" install --pre --root "$DESTDIR" --prefix /usr --no-deps "dist/temboard-$VERSION-py3-none-any.whl"
# Vendor dependencies.
pythonv=$("$python" --version |& grep -Po 'Python \K(3\.[0-9]{1,2})')
uv pip install \
	--pre --no-deps \
	--requirement "$TOP_SRCDIR/vendor.txt" \
	"$TOP_SRCDIR/dist/temboard_toolkit-0.0.0-py3-none-any.whl" \
	--target "$DESTDIR/usr/lib/python$pythonv/site-packages/temboardui/_vendor"

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

rpm="temboard-${VERSION}-${RELEASE}.x86_64.rpm"
mv "$rpm" dist/
rpm -qpl "dist/$rpm"
if [ "${CI-false}" = "true" ] ; then
	exit 0
fi
yum -q -y --disablerepo='extras*' --disablerepo='pgdg*' --disablerepo='epel*' --disablerepo='powertools*' install "dist/$rpm"
(
	cd /
	temboard --version
	test -f /usr/lib/python*/site-packages/temboardui/static/dist/.vite/manifest.json
	test -x /usr/share/temboard/auto_configure.sh
	test -f /usr/lib/systemd/system/temboard.service
)
