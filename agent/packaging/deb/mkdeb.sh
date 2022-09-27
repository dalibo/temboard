#!/bin/bash -eux

TOP_SRCDIR=$(readlink -m "$0/../../..")
UID_GID=$(stat -c %u:%g "$0")
cd "$TOP_SRCDIR"
test -f setup.py

BUILDDIR=$(readlink -m packaging/deb/build)
DESTDIR=$BUILDDIR/destdir

teardown () {
    set +x
    if [ "0" = "${CLEAN-1}" ] ; then
        return
    fi

    rm -rf "$BUILDDIR"

    if type -p temboard-agent &>/dev/null ; then
        echo "Cleaning previous installation." >&2
        apt-get -qq purge -y temboard-agent
    fi
    set -x
}
trap teardown EXIT INT TERM
teardown

mkdir -p "$DESTDIR"

#       V E R S I O N S

if [ -z "${VERSION-}" ] ; then
	VERSION=$(python3 setup.py --version)
fi
mapfile -t versions < <(pep440deb --echo "$VERSION" | tr ' ' '\n')
pep440v=${versions[0]}
debianv=${versions[1]}
codename=$(lsb_release --codename --short)
release=0dlb1${codename}1

#       I N S T A L L

whl="dist/temboard_agent-$pep440v-py3-none-any.whl"
if ! [ -f "$whl" ] ; then
	pip download --only-binary :all: --no-deps --pre --dest "dist/" "temboard-agent==$pep440v"
fi

# Install from sources
pip3 install --pre --root "$DESTDIR" --prefix /usr --no-deps --no-compile "$whl"
# Fake --install-layout=deb, when using wheel.
pythonv=$(python3 --version |& grep -Po 'Python \K([3]\..)')
mkdir -p "${DESTDIR}/usr/lib/python3/dist-packages/"
mv "$DESTDIR/usr/lib/python${pythonv}/site-packages"/* "$DESTDIR/usr/lib/python3/dist-packages/"

#       B U I L D

fpm_args=()
case "$codename" in
	stretch)
	;;
	*)
		fpm_args+=(--depends python3-distutils)
	;;
esac

fpm --verbose \
    --force \
    --debug-workspace \
    --chdir "$DESTDIR" \
    --input-type dir \
    --output-type deb \
    --name temboard-agent \
    --version "$debianv" \
    --iteration "$release" \
    --architecture all \
    --description "PostgreSQL Remote Control Agent" \
    --category database \
    --maintainer "${DEBFULLNAME} <${DEBEMAIL}>" \
    --license PostgreSQL \
    --url https://labs.dalibo.com/temboard/ \
    --depends python3 \
    --depends python3-bottle \
    --depends python3-cryptography \
    --depends python3-pkg-resources \
    --depends 'python3-psycopg2 >= 2.7' \
    --depends python3-setuptools \
    --depends ssl-cert \
    --after-install share/restart-all.sh \
    "$@" \
    ./=/

#       T E S T

deb="temboard-agent_${debianv}-${release}_all.deb"
mv "$deb" dist/
dpkg-deb --info "dist/$deb"
dpkg-deb --show --showformat '$''{Depends}\n' "dist/$deb"
dpkg-deb --contents "dist/$deb"
if grep -q stretch /etc/os-release ; then
	# Debian has only python3-psycopg2 2.6. Use python3-psycopg2 >2.7 from PGDG.
	curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/apt.postgresql.org.gpg
	echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
fi
apt-get update --quiet
apt-get install --yes "./dist/$deb"
(
	cd /
	temboard-agent --version
)

#       S A V E

# Point deb as latest build for changes generation.
ln -fs "$deb" "dist/temboard-agent_last.deb"
chown -R "${UID_GID}" "dist/"
