#!/bin/bash -eux
# use CLEAN=0 to avoid the final teardown tidoudou dou

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
codename=$(grep -Po 'VERSION_CODENAME=\K(.+)' /etc/os-release)
release="0dlb1${codename}1"

#       I N S T A L L

export PIP_CACHE_DIR=build/pip-cache/
dist="$DISTDIR/temboard-$pep440v"-py2.py3-none-any.whl
if ! [ -f "$dist" ] ; then
	pip3 download --only-binary :all: --no-deps --pre --dest "$DISTDIR/" "temboard==$pep440v"
fi

pip3 install --ignore-installed --root "$DESTDIR/" --only-binary cffi,cryptography "$dist"
# Follows a list of hacks to make pip install result FHS compliant while
# keeping temboard dependencies private.
#
# --prefix and --root does not work together. Let's fix this.
mv "$DESTDIR/usr/local/share" "$DESTDIR/usr/"
# Move temboard out of FHS.
mkdir "$DESTDIR/usr/lib"
mv "$DESTDIR/usr/local/lib"/*/dist-packages  "$DESTDIR/usr/lib/temboard"
mv "$DESTDIR/usr/local/lib/systemd"  "$DESTDIR/usr/lib"
# Move binaries out of FHS.
mv "$DESTDIR/usr/local/bin" "$DESTDIR/usr/lib/temboard/"
rm -rf "${DESTDIR:?}/usr/local"

# Create FHS wrapper.
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

(
	export DEBIANV=$debianv
	export RELEASE=$release
	export PYTHON_PKG=$python_pkg
	ARCH=$(dpkg-architecture --query DEB_HOST_ARCH)
	export ARCH
	nfpm pkg --config packaging/deb/nfpm.yaml --packager deb
)

#       T E S T

deb="$(ls "temboard_${debianv}-${release}_"*.deb)"
dpkg-deb -I "$deb"
dpkg-deb -c "$deb"
apt-get update --yes --quiet
apt-get install --yes --no-install-recommends "./$deb"
(
	cd /
	temboard --version
	test -f /usr/lib/temboard/temboardui/static/dist/.vite/manifest.json
	test -x /usr/share/temboard/auto_configure.sh
	test -f /usr/lib/systemd/system/temboard.service
)

#       S A V E

mkdir -p "$DISTDIR/"
mv -fv "$deb" "$DISTDIR/"
# Point deb as latest build for changes generation.
ln -fs "$(basename "$deb")" "$DISTDIR/temboard_last.deb"
chown -R "$UID_GID" "$DISTDIR/"*
