#!/bin/sh -eux

if ! getent group reprepro ; then
    addgroup -g 600 reprepro
fi

adduser nginx reprepro

exec nginx -g 'daemon off;'
