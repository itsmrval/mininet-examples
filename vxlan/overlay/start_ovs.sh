#!/bin/bash
set -e

mkdir -p /var/run/openvswitch /etc/openvswitch
[ -f /etc/openvswitch/conf.db ] || \
    ovsdb-tool create /etc/openvswitch/conf.db /usr/share/openvswitch/vswitch.ovsschema

ovsdb-server \
    --remote=punix:/var/run/openvswitch/db.sock \
    --remote=db:Open_vSwitch,Open_vSwitch,manager_options \
    --pidfile=/var/run/openvswitch/ovsdb-server.pid \
    --detach 2>/dev/null || true

ovs-vsctl --no-wait init

ovs-vswitchd \
    --pidfile=/var/run/openvswitch/ovs-vswitchd.pid \
    --detach \
    unix:/var/run/openvswitch/db.sock 2>/dev/null || true
