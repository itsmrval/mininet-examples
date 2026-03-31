#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import Node
from mininet.cli import CLI
from mininet.log import setLogLevel
import os
import time
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class LinuxRouter(Node):
    def config(self, **params):
        super().config(**params)
        self.cmd('sysctl -w net.ipv4.ip_forward=1')

def install_frr_configs():
    for node in ['r1', 'r2']:
        src = f"{SCRIPT_DIR}/conf/{node}"
        dst = f"/etc/frr/{node}"
        log = f"/var/log/frr/{node}"
        os.makedirs(dst, exist_ok=True)
        os.makedirs(log, exist_ok=True)
        for f in os.listdir(src):
            shutil.copy(f"{src}/{f}", dst)
        os.system(f'chown -R frr:frr {dst} {log}')

def run():
    os.system('systemctl stop frr 2>/dev/null')
    install_frr_configs()

    net = Mininet()

    r1 = net.addHost('r1', cls=LinuxRouter, ip=None)
    r2 = net.addHost('r2', cls=LinuxRouter, ip=None)
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    h1 = net.addHost('h1', ip='192.168.1.10/24', defaultRoute='via 192.168.1.1')
    h2 = net.addHost('h2', ip='192.168.2.10/24', defaultRoute='via 192.168.2.1')

    net.addLink(h1, s1)
    net.addLink(s1, r1, intfName2='r1-eth0')
    net.addLink(r1, r2, intfName1='r1-eth1', intfName2='r2-eth1')
    net.addLink(r2, s2, intfName1='r2-eth0')
    net.addLink(s2, h2)

    net.start()

    # fix for standalone mode
    os.system('ovs-vsctl set-fail-mode s1 standalone')
    os.system('ovs-vsctl set-fail-mode s2 standalone')

    r1.cmd('ip addr add 192.168.1.1/24 dev r1-eth0')
    r1.cmd('ip addr add 192.168.12.1/30 dev r1-eth1')
    r2.cmd('ip addr add 192.168.2.1/24 dev r2-eth0')
    r2.cmd('ip addr add 192.168.12.2/30 dev r2-eth1')

    r1.cmd('/usr/lib/frr/frrinit.sh start r1')
    r2.cmd('/usr/lib/frr/frrinit.sh start r2')

    print("*** Timeout (10s)...")
    time.sleep(10)

    CLI(net)

    r1.cmd('/usr/lib/frr/frrinit.sh stop r1')
    r2.cmd('/usr/lib/frr/frrinit.sh stop r2')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
