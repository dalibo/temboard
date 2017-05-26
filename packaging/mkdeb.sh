#!/bin/bash -eu

cd $(readlink -m $0/..)

teardown () {
    if [ "0" = "${CLEAN-1}" ] ; then
        return
    fi

    rm -rf $WORKDIR

    echo "Cleaning previous installation." >&2
    if hash temboard ; then
        apt-get purge -y temboard
    fi
}

if [ -z "$(find /var/lib/apt/lists/ -type f)" ] ; then
   apt-get update -y
fi

apt-get install -y --no-install-recommends \
        build-essential \
        lsb-release \
        python2.7 \
        python-pip \
        python-setuptools \
        ruby \
        ruby-dev \
        rubygems \
        ${NULL-}

CODENAME=$(lsb_release --short --codename)
WORKDIR=$(readlink -m build-$CODENAME)
DESTDIR=$WORKDIR/destdir

trap teardown EXIT INT TERM
teardown

pip install -U pip packaging pep440deb virtualenv virtualenv-tools
hash -r pip
gem install --no-ri --no-rdoc fpm

mkdir -p $DESTDIR
versions=($(pep440deb --echo --pypi temboard))
pep440v=${versions[0]}
debianv=${versions[1]}

virtualenv --python=python2.7 $DESTDIR/opt/temboard
export PATH=$DESTDIR/opt/temboard/bin:$PATH
hash -r pip
pip install -U pip setuptools
pip install --pre temboard==$pep440v
pushd $DESTDIR/opt/temboard
virtualenv-tools --update-path /opt/temboard
popd

sed -i s,$DESTDIR,, $DESTDIR/opt/temboard/bin/temboard
mkdir -p $DESTDIR/usr/bin
ln -fsv /opt/temboard/bin/temboard $DESTDIR/usr/bin/temboard
mv $DESTDIR/opt/temboard/share/temboard/* $DESTDIR/opt/temboard/share
rmdir $DESTDIR/opt/temboard/share/temboard

# Let FPM manage .service
find $DESTDIR -name "*.service" -delete

fpm_args=()
if hash systemctl ; then
    fpm_args+="--deb-systemd temboard.service"
else
    fpm_args+="--deb-init temboard.init"
fi

fpm --verbose \
    --debug-workspace \
    --workdir=$WORKDIR \
    --input-type dir \
    --output-type deb \
    --force \
    --architecture $(dpkg-architecture --query DEB_HOST_ARCH) \
    --name temboard \
    --version $debianv \
    --iteration 0dlb1${CODENAME}1 \
    --maintainer "${DEBFULLNAME} <${DEBEMAIL}>" \
    --license PostgreSQL \
    --description "Administration & monitoring PostgreSQL." \
    --url http://temboard.io/ \
    --category database \
    --depends python2.7 \
    ${fpm_args[*]} \
    $DESTDIR/=/

deb=$(ls temboard_*-0dlb1*_*.deb)
dpkg-deb -I $deb
dpkg-deb -c $deb
dpkg -i $deb

mv -fv $deb /dist/
ln -fs $(basename $deb) /dist/last_build_$CODENAME.deb
chown -R $(stat -c %u:%g $0) /dist/*
