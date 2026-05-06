#!/usr/bin/env python3

from mininet.net import Containernet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from functools import partial
import os
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run():
    os.system('docker rm -f r1 r2 r3 2>/dev/null')

    OVS13 = partial(OVSSwitch, protocols='OpenFlow13')
    net = Containernet(controller=RemoteController, switch=OVS13)

    net.addController('c0', controller=RemoteController,
                      ip='127.0.0.1', port=6653)

    docker_opts = dict(dimage='frrouting/frr:latest', privileged=True,
                       cap_add=['ALL'])

    r1 = net.addDocker('r1', ip=None,
                       volumes=[f'{SCRIPT_DIR}/conf/r1:/etc/frr'],
                       **docker_opts)
    r2 = net.addDocker('r2', ip=None,
                       volumes=[f'{SCRIPT_DIR}/conf/r2:/etc/frr'],
                       **docker_opts)
    r3 = net.addDocker('r3', ip=None,
                       volumes=[f'{SCRIPT_DIR}/conf/r3:/etc/frr'],
                       **docker_opts)

    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')
    s4 = net.addSwitch('s4')
    s5 = net.addSwitch('s5')

    h1 = net.addHost('h1', mac='00:00:00:00:00:01',
                     ip='192.168.2.10/24', defaultRoute='via 192.168.2.1')
    h2 = net.addHost('h2', mac='00:00:00:00:00:02',
                     ip='192.168.3.10/24', defaultRoute='via 192.168.3.1')

    net.addLink(r1, s1, intfName1='r1-eth0', addr1='00:00:00:00:01:01')
    net.addLink(r2, s2, intfName1='r2-eth1', addr1='00:00:00:00:02:02')
    net.addLink(r3, s3, intfName1='r3-eth1', addr1='00:00:00:00:03:02')
    net.addLink(s3, s1)
    net.addLink(s2, s1)
    net.addLink(h1, s4)
    net.addLink(r2, s4, intfName1='r2-eth0', addr1='00:00:00:00:02:01')
    net.addLink(h2, s5)
    net.addLink(r3, s5, intfName1='r3-eth0', addr1='00:00:00:00:03:01')

    net.start()

    os.system('ovs-vsctl set-fail-mode s4 standalone')
    os.system('ovs-vsctl set-fail-mode s5 standalone')

    r1.cmd('ip addr add 192.168.12.1/30 dev r1-eth0')
    r1.cmd('ip addr add 192.168.13.1/30 dev r1-eth0')
    r1.cmd('sysctl -w net.ipv4.ip_forward=1')
    r1.cmd('sysctl -w net.ipv4.conf.r1-eth0.rp_filter=0')
    r1.cmd('sysctl -w net.ipv4.conf.r1-eth0.arp_announce=2')
    r1.cmd('sysctl -w net.ipv4.conf.r1-eth0.arp_ignore=1')

    r2.cmd('ip addr add 192.168.12.2/30 dev r2-eth1')
    r2.cmd('ip addr add 192.168.2.1/24 dev r2-eth0')
    r2.cmd('sysctl -w net.ipv4.ip_forward=1')

    r3.cmd('ip addr add 192.168.13.2/30 dev r3-eth1')
    r3.cmd('ip addr add 192.168.3.1/24 dev r3-eth0')
    r3.cmd('sysctl -w net.ipv4.ip_forward=1')

    for r in (r1, r2, r3):
        r.cmd('/usr/lib/frr/frrinit.sh start')

    time.sleep(30)

    CLI(net)

    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
