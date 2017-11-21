#!/bin/bash -eux

#
# Script to run tests on CentOS
#
# Installation instructions taken from
# https://git.postgresql.org/gitweb/?p=pgrpms.git;a=blob;f=docker/Dockerfile-CentOS7-PG96;h=912e41d3a2f7aa6af8d36688e02f49f0dccb1ad3;hb=HEAD
#

top_srcdir=$(readlink -m $0/../../..)
cd $top_srcdir
# Ensure that setup.py exists (we are correctly located)
test -f setup.py

yum_install() {
    local packages=$*
    yum install -y $packages
    rpm --query --queryformat= $packages
}

yum_install epel-release
yum_install python python2-pip
pip install pytest

install_rpm=${TBD_INSTALL_RPM:-0}

# For circle-ci tests we want to install using RPM
# When launched locally we install via pip
if (( install_rpm == 1 ))
then
    # Search for the proper RPM package
    rpmdist=$(rpm --eval '%dist')
    test -f /tmp/dist/rpm/RPMS/noarch/temboard-agent-*${rpmdist}.noarch.rpm
    yum install -y /tmp/dist/rpm/RPMS/noarch/temboard-agent-*${rpmdist}.noarch.rpm
    rpm --query --queryformat= temboard-agent
else
    pip install -e .
fi


# create a user to launch the tests, cannot be done as root
if ! id testuser > /dev/null 2>&1; then
    useradd --system testuser
fi

python -c 'import urllib; urllib.urlretrieve("https://github.com/tianon/gosu/releases/download/1.10/gosu-amd64", "/usr/local/bin/gosu")'
chmod 0755 /usr/local/bin/gosu

# Remove any .pyc file to avoid errors with pytest and cache
find . -name \*.pyc -delete
TBD_WORKPATH="/tmp" gosu testuser pytest -vs -p no:cacheprovider test/legacy/
