#! /usr/bin/python
#  coding: utf-8

'''
Add queues to Mininet using ovs-vsctl and ovs-ofctl
@Author Ryan Wallner
'''

import os
import sys
import time
import subprocess


class QueueSetting():
    def __init__(self):
        pass

    def find_all(self, a_str, sub_str):
        start = 0
        b_starts = []
        while True:
            start = a_str.find(sub_str, start)
            if start == -1: return b_starts
            #print start
            b_starts.append(start)
            start += 1

    def isroot(self):
        if os.getuid() != 0:
            print "Root permissions required"
            exit()

    def get_port_switch(self):
        cmd = "ovs-vsctl show"
        p = os.popen(cmd).read()
        brdgs = self.find_all(p, "Bridge")
        print brdgs
        switches = []
        for bn in brdgs:
            sw = p[(bn + 8):(bn + 10)]
            switches.append(sw)
        ports = self.find_all(p, "Port")
        prts = []
        for prt in ports:
            prt = p[(prt + 6):(prt + 13)]
            if '"' not in prt:
                print prt
                prts.append(prt)
        return switches, prts

    def set_bandwidth_queue(self):

        switches, ports = self.get_port_switch()
        for sw in switches:
            cmd = "ovs-vsctl set Bridge %s protocols=OpenFlow13" % sw
            q_res = os.popen(cmd).read()
        for port in ports:
            queuecmd = "sudo ovs-vsctl -- set port %s qos=@defaultqos " \
                       "-- --id=@defaultqos create qos type=linux-htb other-config:max-rate=10500000 queues=0=@q0,1=@q1,2=@q2 " \
                       "-- --id=@q0 create queue other-config:min-rate=10500000 other-config:max-rate=10500000 " \
                       "-- --id=@q1 create queue other-config:min-rate=3000000 other-config:max-rate=4000000 " \
                       "-- --id=@q2 create queue other-config:min-rate=0 other-config:max-rate=10000000 " % port
            print 'exec cmd:', queuecmd
            q_res = os.popen(queuecmd).read()

    def set_priority_queue(self):

        switches, ports = self.get_port_switch()
        for sw in switches:
            cmd = "ovs-vsctl set Bridge %s protocols=OpenFlow13" % sw
            q_res = os.popen(cmd).read()
        for port in ports:
            queuecmd = "sudo ovs-vsctl -- set port %s qos=@defaultqos " \
                       "-- --id=@defaultqos create qos type=linux-htb other-config:max-rate=10500000 queues=0=@q0,1=@q1,2=@q2 " \
                       "-- --id=@q0 create queue other-config:priority=1 " \
                       "-- --id=@q1 create queue other-config:priority=10 " \
                       "-- --id=@q2 create queue other-config:priority=20 " % port
            print 'exec cmd:', queuecmd
            q_res = os.popen(queuecmd).read()

    def del_queue(self):
        os.popen("ovs-vsctl --all destroy qos")
        os.popen("ovs-vsctl --all destroy queue")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'error occur, p for priority queue and ' \
              'b for bandwidth guarantee queue' \
              'd for delete the setting'

    if sys.argv[1] in 'pbd':
        queue = QueueSetting()
        queue.isroot()
        if sys.argv[1] == 'p':
            queue.set_priority_queue()
        if sys.argv[1] == 'b':
            queue.set_bandwidth_queue()
        if sys.argv[1] == 'd':
            queue.del_queue()