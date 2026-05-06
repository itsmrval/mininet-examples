#!/usr/bin/env python3

import os
import signal
import subprocess
import time

REMOTE_VTEP = os.environ.get('REMOTE_VTEP', '192.168.1.10')
LOCAL_VTEP  = os.environ.get('LOCAL_VTEP',  '192.168.2.10')
VXLAN_PORT  = 4789
HOSTS = {}

def sh(cmd):
    return subprocess.run(cmd, shell=True)

def ns(name, cmd):
    return sh(f'nsenter -t {HOSTS[name]} -n {cmd}')

def get_ofport(intf):
    return os.popen(f'ovs-vsctl get Interface {intf} ofport').read().strip()

def spawn_host(name):
    proc = subprocess.Popen(['unshare', '--net', 'sleep', 'infinity'])
    HOSTS[name] = proc.pid
    open(f'/tmp/{name}.pid', 'w').write(str(proc.pid))
    with open(f'/usr/local/bin/{name}', 'w') as f:
        f.write(f'#!/bin/sh\nexec nsenter -t $(cat /tmp/{name}.pid) -n "$@"\n')
    os.chmod(f'/usr/local/bin/{name}', 0o755)
    time.sleep(0.2)

def setup():
    sh('/usr/local/bin/start_ovs.sh')
    time.sleep(2)

    spawn_host('h3')
    spawn_host('h4')

    sh('ip link add s2-eth1 type veth peer name h3-eth0')
    sh('ip link add s2-eth2 type veth peer name h4-eth0')
    sh(f'ip link set h3-eth0 netns {HOSTS["h3"]}')
    sh(f'ip link set h4-eth0 netns {HOSTS["h4"]}')

    ns('h3', 'ip link set lo up')
    ns('h3', 'ip link set h3-eth0 address 00:00:00:00:02:03')
    ns('h3', 'ip addr add 10.0.0.2/8 dev h3-eth0')
    ns('h3', 'ip link set h3-eth0 up')
    ns('h3', 'arp -s 10.0.0.1 00:00:00:00:01:01')

    ns('h4', 'ip link set lo up')
    ns('h4', 'ip link set h4-eth0 address 00:00:00:00:02:04')
    ns('h4', 'ip addr add 10.0.0.1/8 dev h4-eth0')
    ns('h4', 'ip link set h4-eth0 up')
    ns('h4', 'arp -s 10.0.0.2 00:00:00:00:01:02')

    sh('ovs-vsctl add-br s2 -- set Bridge s2 fail_mode=standalone protocols=OpenFlow13')
    sh('ovs-vsctl add-port s2 s2-eth1')
    sh('ovs-vsctl add-port s2 s2-eth2')
    sh('ip link set s2-eth1 up')
    sh('ip link set s2-eth2 up')
    sh(f'ovs-vsctl add-port s2 vxlan0 -- set interface vxlan0 type=vxlan '
       f'options:remote_ip={REMOTE_VTEP} options:key=flow options:dst_port={VXLAN_PORT}')
    time.sleep(1)

def apply_flows():
    h3 = get_ofport('s2-eth1')
    h4 = get_ofport('s2-eth2')
    vx = get_ofport('vxlan0')

    sh('ovs-ofctl -O OpenFlow13 del-flows s2')
    sh(f'ovs-ofctl -O OpenFlow13 add-flow s2 "table=0,priority=10,in_port={h3},actions=set_field:100->tun_id,resubmit(,1)"')
    sh(f'ovs-ofctl -O OpenFlow13 add-flow s2 "table=0,priority=10,in_port={h4},actions=set_field:200->tun_id,resubmit(,1)"')
    sh(f'ovs-ofctl -O OpenFlow13 add-flow s2 "table=0,priority=0,actions=resubmit(,1)"')
    sh(f'ovs-ofctl -O OpenFlow13 add-flow s2 "table=1,priority=10,ip,nw_dst=10.0.0.1,tun_id=100,actions=output:{vx}"')
    sh(f'ovs-ofctl -O OpenFlow13 add-flow s2 "table=1,priority=10,ip,nw_dst=10.0.0.2,tun_id=200,actions=output:{vx}"')
    sh(f'ovs-ofctl -O OpenFlow13 add-flow s2 "table=1,priority=10,ip,in_port={vx},tun_id=100,actions=output:{h3}"')
    sh(f'ovs-ofctl -O OpenFlow13 add-flow s2 "table=1,priority=10,ip,in_port={vx},tun_id=200,actions=output:{h4}"')
    sh(f'ovs-ofctl -O OpenFlow13 add-flow s2 "table=1,priority=8,arp,tun_id=100,actions=output:{vx}"')
    sh(f'ovs-ofctl -O OpenFlow13 add-flow s2 "table=1,priority=8,arp,tun_id=200,actions=output:{vx}"')
    sh(f'ovs-ofctl -O OpenFlow13 add-flow s2 "table=1,priority=8,arp,in_port={vx},tun_id=100,actions=output:{h3}"')
    sh(f'ovs-ofctl -O OpenFlow13 add-flow s2 "table=1,priority=8,arp,in_port={vx},tun_id=200,actions=output:{h4}"')
    sh('ovs-ofctl -O OpenFlow13 add-flow s2 "table=1,priority=0,actions=drop"')

def cleanup(*_):
    for name, pid in HOSTS.items():
        sh(f'kill {pid} 2>/dev/null')
        sh(f'rm -f /tmp/{name}.pid /usr/local/bin/{name}')
    sh('ovs-vsctl --if-exists del-br s2')
    raise SystemExit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, cleanup)
    setup()
    apply_flows()
    signal.pause()
