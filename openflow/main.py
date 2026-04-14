#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from functools import partial

def run():
    OVS13 = partial(OVSSwitch, protocols='OpenFlow13')
    net = Mininet(controller=RemoteController, switch=OVS13)

    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    s1 = net.addSwitch('s1')

    h1 = net.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.1/8')
    h2 = net.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.2/8')

    net.addLink(h1, s1)
    net.addLink(h2, s1)

    net.start()

    CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
