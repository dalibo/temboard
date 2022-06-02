#!/bin/bash -eux

# Copie avant de changer parternité et droits.
cp -arv /usr/local/lib/grafana/rootfs/* /

chown -R root:root /etc/grafana
chmod -R a+r /etc/grafana
chown -R grafana: /var/lib/grafana
chown -R grafana: /usr/share/grafana

exec su -s "$SHELL" grafana -c /run.sh
