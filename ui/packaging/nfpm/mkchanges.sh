#!/bin/bash -eu

srcdir=$(readlink -m "$0/..")
DEB=$1
CODENAME=$2
CHANGES=${DEB/.deb/_${CODENAME}.changes}
CODENAME=$CODENAME "$srcdir/simplechanges" $DEB > $CHANGES
debsign $CHANGES
