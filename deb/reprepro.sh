#!/bin/bash -eux

cp -ar --preserve /config-user/* /config

chown -v root:root /config /config/*authorized_keys
chmod -v 0644 /config/*authorized_keys
chown -v 600:root /config/*.gpg
chmod -v 0600 /config/*.gpg

exec /run.sh
