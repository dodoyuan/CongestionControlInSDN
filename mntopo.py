#!/usr/bin/env python
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController
# from mininet.term import makeTerm
# from mininet.link import TCLink

if '__main__' == __name__:

    # net = Mininet(controller=RemoteController,link=TCLink)
    net = Mininet(controller=RemoteController)
    c0 = net.addController('c0', port=6633)
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')
    s4 = net.addSwitch('s4')
    s5 = net.addSwitch('s5')
    s6 = net.addSwitch('s6')
    s7 = net.addSwitch('s7')
    s8 = net.addSwitch('s8')

    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    h3 = net.addHost('h3')
    h4 = net.addHost('h4')
    h5 = net.addHost('h5')
    h6 = net.addHost('h6')
    h7 = net.addHost('h7')
    h8 = net.addHost('h8')

    # net.addLink(s1, h1, bw=100)
    net.addLink(s1, h1)
    net.addLink(s1, h2)
    net.addLink(s1, h3)
    net.addLink(s1, h4)
    net.addLink(s8, h5)
    net.addLink(s8, h6)
    net.addLink(s8, h7)
    net.addLink(s8, h8)

    net.addLink(s1, s2)
    net.addLink(s2, s3)
    net.addLink(s3, s4)
    net.addLink(s4, s8)
    net.addLink(s1, s5)
    net.addLink(s5, s4)
    net.addLink(s5, s6)
    net.addLink(s6, s7)
    net.addLink(s7, s8)

    net.build()
    c0.start()
    s1.start([c0])
    s2.start([c0])
    s3.start([c0])
    s4.start([c0])
    s5.start([c0])
    s6.start([c0])
    s7.start([c0])
    s8.start([c0])

    # net.startTerms()
    CLI(net)
    net.stop()


