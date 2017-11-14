#!/bin/bash -eux

#
# Script to run tests on CentOS
#
# Installation instructions taken from
# https://git.postgresql.org/gitweb/?p=pgrpms.git;a=blob;f=docker/Dockerfile-CentOS7-PG96;h=912e41d3a2f7aa6af8d36688e02f49f0dccb1ad3;hb=HEAD
#

cd /workspace

yum_install() {
    local packages=$*
    yum install -y $packages
    rpm --query --queryformat= $packages
}

yum_install epel-release
yum_install python python2-pip

pip install -e .
pip install pytest

# create a user to launch the tests, cannot be done as root
if ! id testuser > /dev/null 2>&1; then
    useradd --system testuser
fi

python -c 'import urllib; urllib.urlretrieve("https://github.com/tianon/gosu/releases/download/1.10/gosu-amd64", "/usr/local/bin/gosu")'
chmod 0755 /usr/local/bin/gosu

# Remove any .pyc file to avoid errors with pytest and cache
find . -name \*.pyc -delete
TBD_WORKPATH="/tmp" gosu testuser pytest -vs -p no:cacheprovider test/legacy/
