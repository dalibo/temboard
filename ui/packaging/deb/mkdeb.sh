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

PYTHON="$(type -p python3)"
if [ -z "${VERSION-}" ] ; then
	VERSION=$("$PYTHON" setup.py --version)
fi
mapfile -t versions < <(pep440deb --echo "$VERSION" | tr ' ' '\n')

pep440v="${versions[0]}"
debianv="${versions[1]}"
CODENAME="$(lsb_release --short --codename)"
release="0dlb1${CODENAME}1"

#       I N S T A L L

export PIP_CACHE_DIR=build/pip-cache/
VIRTUAL_ENV=$DESTDIR/usr/lib/temboard
virtualenv --python="$PYTHON" "$VIRTUAL_ENV"
export PATH=${VIRTUAL_ENV}/bin:$PATH
hash -r pip
pip --version
pip install -U pip setuptools wheel
dist="$DISTDIR/temboard-$pep440v"-py2.py3-none-any.whl
if ! [ -f "$dist" ] ; then
	pip download --only-binary :all: --no-deps --pre --dest "$DISTDIR/" "temboard==$pep440v"
fi
pip install --only-binary cffi,cryptography "$dist" 'psycopg2-binary<2.9'
pip check
virtualenv --python="$PYTHON" --relocatable "$VIRTUAL_ENV"

sed -i "s,$DESTDIR,," "$VIRTUAL_ENV/bin/temboard"
mkdir -p "$DESTDIR/usr/bin"
ln -fsv ../lib/temboard/bin/temboard "${DESTDIR}/usr/bin/temboard"
mv "$VIRTUAL_ENV/share" "$DESTDIR/usr/share"
mv "$VIRTUAL_ENV/lib/systemd" "$DESTDIR/usr/lib"
pip uninstall --yes pip wheel
export PATH=${PATH#*/bin:}

#       B U I L D

python_pkg="$(dpkg -S "$PYTHON")"
python_pkg="${python_pkg%:*}"
python_pkg="${python_pkg/-minimal}"

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
    --url https://labs.dalibo.com/temboard/ \
    --after-install packaging/deb/postinst.sh \
    --depends "$python_pkg" \
    "$DESTDIR/=/"

#       T E S T

deb="$(ls "temboard_${debianv}-${release}_"*.deb)"
dpkg-deb -I "$deb"
dpkg-deb -c "$deb"
dpkg -i "$deb"
(
	cd /
	temboard --version
	test -f /usr/lib/temboard/lib/python3.*/site-packages/temboardui/static/manifest.json
)

#       S A V E

mkdir -p "$DISTDIR/"
mv -fv "$deb" "$DISTDIR/"
# Point deb as latest build for changes generation.
ln -fs "$(basename "$deb")" "$DISTDIR/temboard_last.deb"
chown -R "$UID_GID" "$DISTDIR/"*
