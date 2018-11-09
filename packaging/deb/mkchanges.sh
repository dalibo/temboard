#!/bin/bash -eu

DEB=$1
CODENAME=$2
CHANGES=${DEB/.deb/_${CODENAME}.changes}
CODENAME=$CODENAME ./simplechanges $DEB > $CHANGES
debsign $CHANGES
