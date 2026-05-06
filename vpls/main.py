#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from functools import partial


class VPLSTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        h1 = self.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.1/8')
        h2 = self.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.2/8')
        h3 = self.addHost('h3', mac='00:00:00:00:00:03', ip='10.0.0.3/8')
        h4 = self.addHost('h4', mac='00:00:00:00:00:04', ip='10.0.0.4/8')

        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s2)
        self.addLink(h4, s2)
        self.addLink(s1, s2)


def run():
    OVS13 = partial(OVSSwitch, protocols='OpenFlow13')
    net = Mininet(topo=VPLSTopo(), switch=OVS13, controller=None)
    net.addController('c0', controller=RemoteController,
                      ip='127.0.0.1', port=6653)

    net.start()
    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
