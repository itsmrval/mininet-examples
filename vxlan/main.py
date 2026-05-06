#!/usr/bin/env python3

from mininet.net import Containernet
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
    for node in ['r1', 'r2', 'r3']:
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

    net = Containernet()

    r1 = net.addHost('r1', cls=LinuxRouter, ip=None)
    r2 = net.addHost('r2', cls=LinuxRouter, ip=None)
    r3 = net.addHost('r3', cls=LinuxRouter, ip=None)

    docker_opts = dict(
        dimage='vxlan-overlay',
        privileged=True,
        cap_add=['ALL'],
        volumes=[f'{SCRIPT_DIR}/overlay:/overlay'],
    )
    d1 = net.addDocker('d1', ip='192.168.1.10/24', defaultRoute='via 192.168.1.1',
                       environment={'LOCAL_VTEP': '192.168.1.10', 'REMOTE_VTEP': '192.168.2.10'},
                       **docker_opts)
    d2 = net.addDocker('d2', ip='192.168.2.10/24', defaultRoute='via 192.168.2.1',
                       environment={'LOCAL_VTEP': '192.168.2.10', 'REMOTE_VTEP': '192.168.1.10'},
                       **docker_opts)

    net.addLink(d1, r1, intfName1='d1-eth0', intfName2='r1-eth0')
    net.addLink(r1, r3, intfName1='r1-eth1', intfName2='r3-eth0')
    net.addLink(r3, r2, intfName1='r3-eth1', intfName2='r2-eth1')
    net.addLink(r2, d2, intfName1='r2-eth0', intfName2='d2-eth0')

    net.start()

    r1.cmd('ip addr add 192.168.1.1/24 dev r1-eth0')
    r1.cmd('ip addr add 203.0.13.1/30 dev r1-eth1')
    r3.cmd('ip addr add 203.0.13.2/30 dev r3-eth0')
    r3.cmd('ip addr add 203.0.23.1/30 dev r3-eth1')
    r2.cmd('ip addr add 203.0.23.2/30 dev r2-eth1')
    r2.cmd('ip addr add 192.168.2.1/24 dev r2-eth0')

    r1.cmd('/usr/lib/frr/frrinit.sh start r1')
    r2.cmd('/usr/lib/frr/frrinit.sh start r2')
    r3.cmd('/usr/lib/frr/frrinit.sh start r3')

    print("*** Timeout (15s)...")
    time.sleep(15)

    d1.cmd('python3 /overlay/d1.py > /tmp/overlay.log 2>&1 &')
    d2.cmd('python3 /overlay/d2.py > /tmp/overlay.log 2>&1 &')
    time.sleep(10)

    CLI(net)

    r1.cmd('/usr/lib/frr/frrinit.sh stop r1')
    r2.cmd('/usr/lib/frr/frrinit.sh stop r2')
    r3.cmd('/usr/lib/frr/frrinit.sh stop r3')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
