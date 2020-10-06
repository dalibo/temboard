#!/bin/bash -eux

UID_GID=$(stat -c %u:%g $0)
cd $(readlink -m $0/..)

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

mkdir -p $DESTDIR

#       V E R S I O N S

versions=($(pep440deb --echo --pypi temboard-agent))
pep440v=${versions[0]}
debianv=${versions[1]}
codename=$(lsb_release --codename --short)
release=0dlb1${codename}1
# Should match the interpreter used by scripts shebang. We should pin python
# version used.
python=/usr/bin/python
pythonv=$($python --version |& grep -Po 'Python \K([23]\..)')

#       I N S T A L L

pip$pythonv install --pre --root $DESTDIR --prefix /usr --no-deps temboard-agent==$pep440v
# Fake --install-layout=deb, when using wheel.
mv $DESTDIR/usr/lib/python${pythonv}/{site,dist}-packages/

#       B U I L D

fpm_args=()
if ! [ -f /usr/bin/systemctl ] ; then
	fpm_args+=(--deb-init temboard-agent.init)
fi

fpm --verbose \
    --force \
    --debug-workspace \
    --chdir $DESTDIR \
    --input-type dir \
    --output-type deb \
    --name temboard-agent \
    --version $debianv \
    --iteration $release \
    --architecture all \
    --description "PostgreSQL Remote Control Agent" \
    --category database \
    --maintainer "${DEBFULLNAME} <${DEBEMAIL}>" \
    --license PostgreSQL \
    --url http://temboard.io/ \
    --depends python-pkg-resources \
    --depends ssl-cert \
    --depends python-psycopg2 \
    --depends python${pythonv} \
    --after-install ../../share/restart-all.sh \
    "${fpm_args[@]}" \
    "$@" \
    ./=/

#       T E S T

deb=$(ls temboard-agent_*-${release}_all.deb)
dpkg-deb -I $deb
dpkg-deb -c $deb
apt-get update --quiet
apt-get install --yes ./$deb
(
	cd /
	temboard-agent --version
	python -c 'import temboardagent.toolkit'
)

#       S A V E

mkdir -p ${DISTDIR}/
mv -fv $deb ${DISTDIR}/
# Point deb as latest build for changes generation.
ln -fs $(basename $deb) ${DISTDIR}/last_build.deb
chown -R ${UID_GID} ${DISTDIR}/
