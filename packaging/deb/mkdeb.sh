#!/bin/bash -eux

cd $(readlink -m $0/..)
TOP_SRCDIR=$(readlink -m "$0/../../..")
UID_GID=$(stat -c %u:%g "$0")

WORKDIR=$(readlink -m build)
DESTDIR=$WORKDIR/destdir
DISTDIR=$(readlink -m ${PWD}/../../dist)

teardown () {
    set +x
    if [ "0" = "${CLEAN-1}" ] ; then
        return
    fi

    rm -rf $WORKDIR

    if hash temboard-agent ; then
        echo "Cleaning previous installation." >&2
        apt-get -qq purge -y temboard-agent
    fi
    set -x
}
trap teardown EXIT INT TERM
teardown

mkdir -p "$DESTDIR"

#       V E R S I O N S

versions=($(pep440deb --echo --pypi temboard-agent))
pep440v=${versions[0]}
debianv=${versions[1]}
codename=$(lsb_release --codename --short)
release=0dlb1${codename}1

#       I N S T A L L

if [ "${FROMSOURCE-}" = 1 ] ;
then
	# Install from sources
	pip3 install --pre --root $DESTDIR --prefix /usr --no-deps --no-compile $TOP_SRCDIR
else
	# Install from pypi
	pip3 install --pre --root $DESTDIR --prefix /usr --no-deps --no-compile temboard-agent==$pep440v
fi
# Fake --install-layout=deb, when using wheel.
pythonv=$(python3 --version |& grep -Po 'Python \K([3]\..)')
mkdir -p "${DESTDIR}/usr/lib/python3/dist-packages/"
mv "$DESTDIR/usr/lib/python${pythonv}/site-packages"/* "$DESTDIR/usr/lib/python3/dist-packages/"

#       B U I L D

fpm_args=()
case "$codename" in
	stretch|wheezy)
		fpm_args+=(--deb-init temboard-agent.init)
	;;
	jessie)
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
    --url http://temboard.io/ \
    --depends python3-pkg-resources \
    --depends ssl-cert \
    --depends 'python3-psycopg2 >= 2.7' \
    --depends python3 \
    --after-install ../../share/restart-all.sh \
    "${fpm_args[@]}" \
    "$@" \
    ./=/

#       T E S T

deb=$(ls temboard-agent_*-${release}_all.deb)
dpkg-deb --info "$deb"
dpkg-deb --show --showformat '${Depends}\n' "$deb"
dpkg-deb --contents "$deb"
if grep -q stretch /etc/os-release ; then
	# Debian has only python3-psycopg2 2.6. Use python3-psycopg2 >2.7 from PGDG.
	curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/apt.postgresql.org.gpg
	echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
fi
apt-get update --quiet
apt-get install --yes "./$deb"
(
	cd /
	temboard-agent --version
	python3 -c 'import temboardagent.toolkit'
)

#       S A V E

mkdir -p ${DISTDIR}/
mv -fv $deb ${DISTDIR}/
# Point deb as latest build for changes generation.
ln -fs "$(basename "$deb")" "${DISTDIR}/temboard-agent_last.deb"
chown -R ${UID_GID} ${DISTDIR}/
