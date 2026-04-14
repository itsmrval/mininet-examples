#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

def run():
    net = Mininet(controller=RemoteController, switch=OVSSwitch)

    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)

    # Switches
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')

    h1 = net.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.1/8')
    h2 = net.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.2/8')
    h3 = net.addHost('h3', mac='00:00:00:00:00:03', ip='10.0.0.3/8')
    h4 = net.addHost('h4', mac='00:00:00:00:00:04', ip='10.0.0.4/8')

    net.addLink(s1, s2)  # s1-eth1 <-> s2-eth3
    net.addLink(s1, s3)  # s1-eth2 <-> s3-eth3

    net.addLink(h1, s2)  # h1-eth0 <-> s2-eth1
    net.addLink(h2, s2)  # h2-eth0 <-> s2-eth2

    net.addLink(h3, s3)  # h3-eth0 <-> s3-eth1
    net.addLink(h4, s3)  # h4-eth0 <-> s3-eth2

    net.start()

    CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
