#!/bin/bash -eu

cd $(readlink -m $0/..)

WORKDIR=$(readlink -m build)
DESTDIR=$WORKDIR/destdir

teardown () {
    if [ "0" = "${CLEAN-1}" ] ; then
        return
    fi

    rm -rf $WORKDIR

    echo "Cleaning previous installation." >&2
    if hash temboard-agent ; then
        apt-get purge -y temboard-agent
    fi
}
trap teardown EXIT INT TERM

genchanges() {
    tar -C $WORKDIR -xvf $(find $WORKDIR -name control.tar.gz) ./control
    cat - $WORKDIR/control > $WORKDIR/control.full <<EOF
Source: temboard-agent

EOF
}

teardown

if [ -z "$(find /var/lib/apt/lists/ -type f)" ] ; then
   apt-get update -y
fi

apt-get install -y --no-install-recommends \
        build-essential \
        python2.7 \
        python-pip \
        ruby \
        ruby-dev \
        rubygems \
        ${NULL-}

pip install -U pip
hash -r pip
pip install -U packaging pep440deb
gem install --no-ri --no-rdoc fpm

mkdir -p $DESTDIR
versions=($(pep440deb --echo --pypi temboard-agent))
pep440v=${versions[0]}
debianv=${versions[1]}

pip install --pre --root $DESTDIR --no-deps --prefix /usr temboard-agent==$pep440v
# Dirty fake of --install-layout=deb. This is required for wheezy and jessie
# where PYTHONPATH does not include site-packages, but only dist-packages.
mv $DESTDIR/usr/lib/python2.7/{site,dist}-packages/
# Let FPM manage .service
find $DESTDIR -name "*.service" -delete

fpm_args=()
if hash systemctl ; then
    fpm_args+="--deb-systemd temboard-agent.service"
else
    fpm_args+="--deb-init temboard-agent.init"
fi

fpm --verbose \
    --chdir $DESTDIR \
    --debug-workspace \
    --input-type dir \
    --output-type deb \
    --force \
    --architecture all \
    --name temboard-agent \
    --version $debianv \
    --iteration 0dlb1 \
    --maintainer "${DEBFULLNAME} <${DEBEMAIL}>" \
    --license PostgreSQL \
    --description "Administration & monitoring PostgreSQL agent." \
    --url http://temboard.io/ \
    --category database \
    --depends python2.7 \
    ${fpm_args[*]} \
    ./=/

deb=$(ls temboard-agent_*-0dlb1_all.deb)
dpkg-deb -I $deb
dpkg-deb -c $deb
dpkg -i $deb

mv -fv $deb /dist/
ln -fs $(basename $deb) /dist/last_build.deb
chown -R $(stat -c %u:%g $0) /dist/
