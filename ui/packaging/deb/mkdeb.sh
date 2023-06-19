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
CLEAN=1 teardown

mkdir -p "$DESTDIR"

#       V E R S I O N S

PYTHON="$(readlink -e "$(type -p python3)")"
if [ -z "${VERSION-}" ] ; then
	VERSION=$("$PYTHON" setup.py --version)
fi
mapfile -t versions < <(pep440deb --echo "$VERSION" | tr ' ' '\n')

pep440v="${versions[0]}"
debianv="${versions[1]}"
# Testing/sid has LSB release as `n\a`. Stable as debian_version as X.Y.
if ! codename=$(grep -Po '(.+(?=/))' /etc/debian_version) ; then
    codename=$(lsb_release --codename --short)
fi
release="0dlb1${codename}1"

#       I N S T A L L

export PIP_CACHE_DIR=build/pip-cache/
dist="$DISTDIR/temboard-$pep440v"-py2.py3-none-any.whl
if ! [ -f "$dist" ] ; then
	pip3 download --only-binary :all: --no-deps --pre --dest "$DISTDIR/" "temboard==$pep440v"
fi
pip3 install --target "$DESTDIR/usr/lib/temboard" --only-binary cffi,cryptography "$dist"

mkdir -p "$DESTDIR/usr/bin"
cat > "$DESTDIR/usr/bin/temboard" <<'EOF'
#!/bin/bash
set -eu
export PYTHONPATH=/usr/lib/temboard
exec /usr/lib/temboard/bin/temboard "$@"
EOF

chmod +x "$DESTDIR/usr/bin/temboard"

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
    --depends python3-psycopg2 \
    "$DESTDIR/=/"

#       T E S T

deb="$(ls "temboard_${debianv}-${release}_"*.deb)"
dpkg-deb -I "$deb"
dpkg-deb -c "$deb"
apt-get update --yes --quiet
apt-get install --yes --no-install-recommends "./$deb"
(
	cd /
	temboard --version
	test -f /usr/lib/temboard/temboardui/static/manifest.json
)

#       S A V E

mkdir -p "$DISTDIR/"
mv -fv "$deb" "$DISTDIR/"
# Point deb as latest build for changes generation.
ln -fs "$(basename "$deb")" "$DISTDIR/temboard_last.deb"
chown -R "$UID_GID" "$DISTDIR/"*
