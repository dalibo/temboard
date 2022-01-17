#!/bin/bash -eux

UID_GID=$(stat -c %u:%g "$0")
cd "$(readlink -m "$0/../../..")"
test -f setup.py

WORKDIR=$(readlink -m build/debian)
DESTDIR=$WORKDIR/destdir
DISTDIR=$(readlink -m dist)

teardown () {
    set +x
    if [ "0" = "${CLEAN-1}" ] ; then
        return
    fi

    rm -rf "$WORKDIR"

    if hash temboard &>/dev/null; then
	echo "Cleaning previous installation." >&2
        apt-get -qq purge -y temboard
    fi
    set -x
}
trap teardown EXIT INT TERM
teardown

mkdir -p "$DESTDIR"

#       V E R S I O N S

pep440deb=(pep440deb --echo)
if [ -n "${VERSION-}" ] ; then
	pep440deb+=("$VERSION")
else
	pep440deb+=(--pypi temboard)
fi
mapfile -t versions < <("${pep440deb[@]}" | tr ' ' '\n')

pep440v="${versions[0]}"
debianv="${versions[1]}"
CODENAME="$(lsb_release --short --codename)"
release="0dlb1${CODENAME}1"

#       I N S T A L L

export PIP_CACHE_DIR=build/pip-cache/
VIRTUAL_ENV=$DESTDIR/usr/lib/temboard
virtualenv --python=python2.7 "$VIRTUAL_ENV"
export PATH=${VIRTUAL_ENV}/bin:$PATH
hash -r pip
pip install -U pip setuptools wheel
dist=${DISTDIR}/temboard-${pep440v}-py2-none-any.whl
if ! [ -f "$dist" ] ; then
	pip download --no-deps --pre --dest "$DISTDIR/" "temboard==$pep440v"
fi
# We have to explicitly install either psycopg2 or psycopg2-binary starting from
# temboard 4.0. For temboard 3.0, use psycopg-2.7 as it matches temboard 3.0
# requirements and have wheel available on PyPI. Once temboard 3.0 is
# deprecated, we can safely change this line to 'psycopg2-binary' and ship
# latest psycopg2.
pip install "$dist" 'psycopg2<2.8'
pip check
virtualenv --python=python2.7 --relocatable "$VIRTUAL_ENV"

sed -i "s,$DESTDIR,," "$VIRTUAL_ENV/bin/temboard"
mkdir -p "$DESTDIR/usr/bin"
ln -fsv ../lib/temboard/bin/temboard "${DESTDIR}/usr/bin/temboard"
ln -fsv ../lib/temboard/bin/temboard-migratedb "${DESTDIR}/usr/bin/temboard-migratedb"
mv "$VIRTUAL_ENV/share" "$DESTDIR/usr/share"
mv "$VIRTUAL_ENV/lib/systemd" "$DESTDIR/usr/lib"
pip uninstall --yes pip wheel
export PATH=${PATH#*/bin:}

#       B U I L D

fpm --verbose \
    --force \
    --debug-workspace \
    --workdir="$WORKDIR" \
    --input-type dir \
    --output-type deb \
    --name temboard \
    --version "$debianv" \
    --iteration "$release" \
    --architecture "$(dpkg-architecture --query DEB_HOST_ARCH)" \
    --description "PostgreSQL Remote Control UI" \
    --category database \
    --maintainer "${DEBFULLNAME} <${DEBEMAIL}>" \
    --license PostgreSQL \
    --url http://temboard.io/ \
    --after-install packaging/deb/postinst.sh \
    --depends python2.7 \
    "$DESTDIR/=/"

#       T E S T

deb="$(ls "temboard_${debianv}-${release}_"*.deb)"
dpkg-deb -I "$deb"
dpkg-deb -c "$deb"
dpkg -i "$deb"
(
	cd /
	temboard --version
	/usr/lib/temboard/bin/python -c 'import temboardui.toolkit'
)

#       S A V E

mkdir -p "$DISTDIR/"
mv -fv "$deb" "$DISTDIR/"
# Point deb as latest build for changes generation.
ln -fs "$(basename "$deb")" "$DISTDIR/temboard_last.deb"
chown -R "$UID_GID" "$DISTDIR/"*
