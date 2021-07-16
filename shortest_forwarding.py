# coding=utf-8
# Copyright (C) 2016 Li Cheng at Beijing University of Posts
# and Telecommunications. www.muzixing.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# import logging
# import struct
# import networkx as nx
# from operator import attrgetter
# from ryu import cfg
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
# from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib import hub
# from ryu.topology import event, switches
# from ryu.topology.api import get_switch, get_link
from collections import defaultdict
import network_awareness
import network_monitor
# import network_delay_detector
import setting
from network_reconfigration import milp_sdn_routing, max_admittable_flow
from copy import deepcopy
from NSGA2.NSGA_Network_Model import NetModel


class ShortestForwarding(app_manager.RyuApp):
    """
        ShortestForwarding is a Ryu app for forwarding packets in shortest
        path.
        This App does not defined the path computation method.
        To get shortest path, this module depends on network awareness,
        network monitor and network delay detecttor modules.
    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {
        "network_awareness": network_awareness.NetworkAwareness,
        "network_monitor": network_monitor.NetworkMonitor,
        # "network_delay_detector": network_delay_detector.NetworkDelayDetector
        }

    WEIGHT_MODEL = {'hop': 'weight', "delay": "delay", "bw": "bw"}

    def __init__(self, *args, **kwargs):
        super(ShortestForwarding, self).__init__(*args, **kwargs)
        self.name = 'shortest_forwarding'
        self.awareness = kwargs["network_awareness"]
        self.monitor = kwargs["network_monitor"]
        # self.delay_detector = kwargs["network_delay_detector"]
        self.datapaths = {}
        self.weight = self.WEIGHT_MODEL[setting.WEIGHT]
        # below is data for ilp process

        # self.ilp_module_thread = hub.spawn(self._ilp_process)
        self.flow = defaultdict(list)   # (eth_type, ip_pkt.src, ip_pkt.dst, in_port)-->
                                        # [require_band, priority,(src,dst)]
        # self.flow_ip = []
        self.lookup = {}   # (src,dst) --> (eth_type, ip_pkt.src, ip_pkt.dst, in_port)
        self.count = 1
        self.config_priority = 2  #
        self.congstion = 0
        self.handle_flag = 0
        self.flow_path = {}

    def set_weight_mode(self, weight):
        """
            set weight mode of path calculating.
        """
        self.weight = weight
        if self.weight == self.WEIGHT_MODEL['hop']:
            self.awareness.get_shortest_paths(weight=self.weight)
        return True

    def _ilp_process(self, chosen_flow, mode):
        '''
            the entry for ilp process
        '''
        # if flag is 1,denote there must be congestion
        # self.logger.debug("config_flag:%s handle-flag %s" % (self.config_flag, self.handle_flag))
        if self.handle_flag:
            self.logger.info("enter re-configration, process with mode: %s", mode)
            self.monitor.res_bw_show()
            self.handle_flag = 0  # avoid handle repeat request
            self.congstion = 0

            # allpath, flow_identity, max_priority = self.reconfigration()
            chosen_path, flow_paths = self.routing_alogrithm(chosen_flow, mode)
            self.logger.info('chosen path: %s', str(chosen_path))
            self.logger.info('flow path: %s', str(flow_paths))
            self.config_priority += 1
            for flow, value in chosen_path.items():
                flow_info = self.lookup[flow]
                path = flow_paths[flow][int(value)]
                self.flow_path[flow][1] = path
                # update the res bd
                self.monitor.update_res_bw(path, self.flow_path[flow][2])
                self.logger.info("handle flow : %s chosen_path: %s" % (flow, path))
                self.install_flow(self.datapaths,
                                  self.awareness.link_to_port,
                                  self.awareness.access_table, path,
                                  flow_info, None, prio=self.config_priority)

            # print (information)
            self.logger.info("process finished")
            self.monitor.res_bw_show()

    def add_drop_flow(self, flow_info, prio):
        '''

        '''
        dp_id = self.flow[flow_info][2][0]
        datapath = self.datapaths[dp_id]
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(
            in_port=flow_info[3], eth_type=flow_info[0],
            ipv4_src=flow_info[1], ipv4_dst=flow_info[2])

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_CLEAR_ACTIONS, [])]
        mod = parser.OFPFlowMod(datapath=datapath, priority=prio,
                                idle_timeout=15,
                                hard_timeout=60,
                                flags=ofproto.OFPFF_SEND_FLOW_REM,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    def show_ilp_data(self):
        '''
            show the information ilp module use
        '''
        self.logger.info('-----------require QoS flow info----------------')
        for key, flow in self.flow.items():
            self.logger.info("key:%s '--->'flow:%s" % (key, flow))
            # self.logger.info('ip info (src dst): %s' % key[1:3])
        self.logger.info('-----------info end----------------------')

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        """
            Collect datapath information.
        """
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def add_flow(self, dp, p, match, actions, idle_timeout=0, hard_timeout=0):
        """
            Send a flow entry to datapath.
        """
        ofproto = dp.ofproto
        parser = dp.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        # SET flags=ofproto.OFPFF_SEND_FLOW_REM to inform controller about flow remove
        mod = parser.OFPFlowMod(datapath=dp, priority=p,
                                idle_timeout=idle_timeout,
                                hard_timeout=hard_timeout,
                                flags=ofproto.OFPFF_SEND_FLOW_REM,
                                match=match, instructions=inst)
        dp.send_msg(mod)

    def send_flow_mod(self, datapath, flow_info, src_port, dst_port, prio=1):
        """
            Build flow entry, and send it to datapath.
        """
        parser = datapath.ofproto_parser
        actions = []
        # actions.append(parser.OFPActionSetQueue(queue_num))
        actions.append(parser.OFPActionOutput(dst_port))

        match = parser.OFPMatch(
            in_port=src_port, eth_type=flow_info[0],
            ipv4_src=flow_info[1], ipv4_dst=flow_info[2])

        self.add_flow(datapath, prio, match, actions,
                      idle_timeout=15, hard_timeout=60)

    def _build_packet_out(self, datapath, buffer_id, src_port, dst_port, data):
        """
            Build packet out object.
        """
        actions = []
        if dst_port:
            actions.append(datapath.ofproto_parser.OFPActionOutput(dst_port))

        msg_data = None
        if buffer_id == datapath.ofproto.OFP_NO_BUFFER:
            if data is None:
                return None
            msg_data = data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=buffer_id,
            data=msg_data, in_port=src_port, actions=actions)
        return out

    def send_packet_out(self, datapath, buffer_id, src_port, dst_port, data):
        """
            Send packet out packet to assigned datapath.
        """
        out = self._build_packet_out(datapath, buffer_id,
                                     src_port, dst_port, data)
        if out:
            datapath.send_msg(out)

    def get_port(self, dst_ip, access_table):
        """
            Get access port if dst host.
            access_table: {(sw,port) :(ip, mac)}
        """
        if access_table:
            if isinstance(access_table.values()[0], tuple):
                for key in access_table.keys():
                    if dst_ip == access_table[key][0]:
                        dst_port = key[1]
                        return dst_port
        return None

    def get_port_pair_from_link(self, link_to_port, src_dpid, dst_dpid):
        """
            Get port pair of link, so that controller can install flow entry.
        """
        if (src_dpid, dst_dpid) in link_to_port:
            return link_to_port[(src_dpid, dst_dpid)]
        else:
            self.logger.info("dpid:%s->dpid:%s is not in links" % (
                             src_dpid, dst_dpid))
            return None

    def flood(self, msg):
        """
            Flood ARP packet to the access port
            which has no record of host.
        """
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        for dpid in self.awareness.access_ports:
            for port in self.awareness.access_ports[dpid]:
                if (dpid, port) not in self.awareness.access_table.keys():
                    datapath = self.datapaths[dpid]
                    out = self._build_packet_out(
                        datapath, ofproto.OFP_NO_BUFFER,
                        ofproto.OFPP_CONTROLLER, port, msg.data)
                    datapath.send_msg(out)
        self.logger.debug("Flooding msg")

    def arp_forwarding(self, msg, src_ip, dst_ip):
        """ Send ARP packet to the destination host,
            if the dst host record is existed,
            else, flow it to the unknow access port.
        """
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        result = self.awareness.get_host_location(dst_ip)
        if result:  # host record in access table.
            datapath_dst, out_port = result[0], result[1]
            datapath = self.datapaths[datapath_dst]
            out = self._build_packet_out(datapath, ofproto.OFP_NO_BUFFER,
                                         ofproto.OFPP_CONTROLLER,
                                         out_port, msg.data)
            datapath.send_msg(out)
            self.logger.debug("Reply ARP to knew host")
        else:
            self.flood(msg)

    def get_path(self, src, dst, require_band, weight ):
        """
            Get shortest path from network awareness module.
        """
        shortest_paths = self.awareness.shortest_paths
        # graph = self.awareness.graph
        if weight == self.WEIGHT_MODEL['hop']:
            return shortest_paths.get(src).get(dst)[0]
        elif weight == self.WEIGHT_MODEL['bw']:
            path = shortest_paths[src][dst]
            bw_guarantee_path = self.monitor.get_bw_guaranteed_path(path, require_band)

            return bw_guarantee_path

    def get_sw(self, dpid, in_port, src, dst):
        """
            Get pair of source and destination switches.
        """
        src_sw = dpid
        dst_sw = None

        src_location = self.awareness.get_host_location(src)
        if in_port in self.awareness.access_ports[dpid]:
            if (dpid,  in_port) == src_location:
                src_sw = src_location[0]
            else:
                return None

        dst_location = self.awareness.get_host_location(dst)
        if dst_location:
            dst_sw = dst_location[0]

        return src_sw, dst_sw

    def install_flow(self, datapaths, link_to_port, access_table, path,
                     flow_info, buffer_id, data=None, prio=1):
        '''
            Install flow entires for roundtrip: go and back.
            @parameter: path=[dpid1, dpid2...]
                        flow_info=(eth_type, src_ip, dst_ip, in_port)
        '''
        if path is None or len(path) == 0:
            self.logger.info("Path error!")
            return
        in_port = flow_info[3]
        first_dp = datapaths[path[0]]
        # out_port = first_dp.ofproto.OFPP_LOCAL
        back_info = (flow_info[0], flow_info[2], flow_info[1])

        # inter_link
        if len(path) > 2:
            for i in xrange(1, len(path)-1):
                port = self.get_port_pair_from_link(link_to_port,
                                                    path[i-1], path[i])
                port_next = self.get_port_pair_from_link(link_to_port,
                                                         path[i], path[i+1])
                if port and port_next:
                    src_port, dst_port = port[1], port_next[0]
                    datapath = datapaths[path[i]]
                    self.send_flow_mod(datapath, flow_info, src_port, dst_port, prio)
                    self.send_flow_mod(datapath, back_info, dst_port, src_port, prio)
                    self.logger.debug("inter_link flow install")
        if len(path) > 1:
            # the last flow entry: tor -> host
            port_pair = self.get_port_pair_from_link(link_to_port,
                                                     path[-2], path[-1])
            if port_pair is None:
                self.logger.info("Port is not found")
                return
            src_port = port_pair[1]

            dst_port = self.get_port(flow_info[2], access_table)
            if dst_port is None:
                self.logger.info("Last port is not found.")
                return

            last_dp = datapaths[path[-1]]
            self.send_flow_mod(last_dp, flow_info, src_port, dst_port, prio)
            self.send_flow_mod(last_dp, back_info, dst_port, src_port, prio)

            # the first flow entry
            port_pair = self.get_port_pair_from_link(link_to_port,
                                                     path[0], path[1])
            if port_pair is None:
                self.logger.info("Port not found in first hop.")
                return
            out_port = port_pair[0]
            self.send_flow_mod(first_dp, flow_info, in_port, out_port, prio)
            self.send_flow_mod(first_dp, back_info, out_port, in_port, prio)
            if prio == 1:
                self.send_packet_out(first_dp, buffer_id, in_port, out_port, data)

        # src and dst on the same datapath
        else:
            out_port = self.get_port(flow_info[2], access_table)
            if out_port is None:
                self.logger.info("Out_port is None in same dp")
                return
            self.send_flow_mod(first_dp, flow_info, in_port, out_port, prio)
            self.send_flow_mod(first_dp, back_info, out_port, in_port, prio)
            if prio == 1:
                self.send_packet_out(first_dp, buffer_id, in_port, out_port, data)

    def shortest_forwarding(self, msg, eth_type, ip_src, ip_dst, require_band):
        """
            To calculate shortest forwarding path and install them into datapaths.

        """
        datapath = msg.datapath
        # ofproto = datapath.ofproto
        # parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        result = self.get_sw(datapath.id, in_port, ip_src, ip_dst)
        if result:
            src_sw, dst_sw = result[0], result[1]
            if dst_sw:
                # self.logger.info("src %s dst %s " % (src_sw, dst_sw))
                path = self.get_path(src_sw, dst_sw, require_band, weight=self.weight)
                if (ip_src, ip_dst) in self.flow_path and len(self.flow_path[(ip_src, ip_dst)]) == 1:
                    self.flow_path[(ip_src, ip_dst)].extend([path, require_band])
                    self.logger.info("[PATH]%s<-->%s: %s" % (ip_src, ip_dst, path))
                    # update residual bandwidth here and return network status
                    # ATTENTION: easy cause repeated calculation
                    self.congstion = self.monitor.update_res_bw_and_congestion_detect(path, require_band)
                flow_info = (eth_type, ip_src, ip_dst, in_port)
                # install flow entries to datapath along side the path.
                self.install_flow(self.datapaths,
                                  self.awareness.link_to_port,
                                  self.awareness.access_table, path,
                                  flow_info, msg.buffer_id, msg.data, 1)

        if self.congstion:
            self.logger.info("congestion happen")
            # if congestion,get the flow to reroute
            chose_flow = self.get_interfere_flow()  # get the flow route on congestion path
            if chose_flow != {}:
                self.logger.info('chosen flow: %s', str(chose_flow))
                self.monitor.residual_bandwidth(chose_flow.values())  # renew/update the network res_bw graph
                self._ilp_process(chose_flow, setting.mode)
            else:
                self.logger.info('congestion happend but no flow is chosen')
        return

    def get_interfere_flow(self):
        '''
           if congestion happened, use the located link and flow path information,
           get the flows to reroute
        '''
        congestion_info = self.monitor.congest_link
        link = congestion_info[0]
        bw = congestion_info[1]
        chose_flow = {}
        for key, value in self.flow_path.items():
            path = value[1]
            require_band = value[2]
            assert len(path) > 1
            for i in xrange(len(path)-1):
                if (path[i], path[i+1]) == link or (path[i+1], path[i]) == link:
                    chose_flow[key] = value
                    bw += require_band
                    # 取出链路多少合适，设置剩余带宽为容量的 40% 即可
                    # TODO: 每条链路最大容量不一样如何处理
                    if bw > setting.MAX_CAPACITY * 0.4:  # reasonable value to set
                        return chose_flow
        return {}

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        '''
            In packet_in handler, we need to learn access_table by ARP.
            Therefore, the first packet from UNKOWN host MUST be ARP.
        '''
        msg = ev.msg
        datapath = msg.datapath
        # in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        if isinstance(arp_pkt, arp.arp):
            self.logger.debug("ARP processing")
            self.arp_forwarding(msg, arp_pkt.src_ip, arp_pkt.dst_ip)

        if isinstance(ip_pkt, ipv4.ipv4):
            self.logger.debug("IPV4 processing")
            if len(pkt.get_protocols(ethernet.ethernet)):
                eth_type = pkt.get_protocols(ethernet.ethernet)[0].ethertype
                require_band = 0  # no QoS require data
                # set_queue = 2
                if ip_pkt.src in setting.require_band.keys():  # QoS data
                    require_band = setting.require_band[ip_pkt.src]
                    # set_queue = 0
                    self.ilp_data_handle(ip_pkt, eth_type, datapath.id, require_band)
                self.shortest_forwarding(msg, eth_type, ip_pkt.src, ip_pkt.dst, require_band)

    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def _flow_removed_handler(self, ev):
        '''
            In flow removed handler, get the ip address and unregister in
            the flow dict.
        '''
        self.logger.info("flow removed handler")
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        if msg.reason == ofp.OFPRR_IDLE_TIMEOUT or msg.reason == ofp.OFPRR_HARD_TIMEOUT:
            flow_dst = msg.match.get('ipv4_dst')
            flow_src = msg.match.get('ipv4_src')
            # flow_inport = msg.match.get('in_port')
            if (flow_src, flow_dst) in self.flow_path:
                flow = self.lookup[(flow_src, flow_dst)]
                self.logger.info("del flow info :%s" % str(flow))
                del self.flow[flow]
                self.monitor.residual_bandwidth([self.flow_path[(flow_src, flow_dst)]])  #
                self.monitor.res_bw_show()
                del self.flow_path[(flow_src, flow_dst)]
                del self.lookup[(flow_src, flow_dst)]
                self.count -= 1
                self.show_ilp_data()

    def routing_alogrithm(self, chosen_flow, mode = 'MILP'):
        '''
            chosen_flow --->  chose_flow[(ipsrc, ipdst)] = [(src_dp,dst_dp)， path, require_band]
            prepare the information for ILP model
            we design two algorithm to achieve our purpose.
        '''
        flow_require = {}
        for flow, value in chosen_flow.items():
            flow_require[flow] = value[2]
        res_bw = self.monitor.res_bw  # graph_res_bw[src][dst]['bandwidth'] =

        # (eth_type, ip_pkt.src, ip_pkt.dst, in_port)--> [require_band,priority,(src_dp,dst_dp)]
        # self.flow[(eth_type, ip_pkt.src, ip_pkt.dst, in_port)] = flow_info
        nPath = defaultdict(list)
        path_number = setting.path_number
        shortest_paths = self.awareness.shortest_paths
        for flow, value in chosen_flow.items():
            path = shortest_paths[value[0][0]][value[0][1]][:path_number]
            nPath[flow].extend(path)

        # target: len(nPath[flow]) == n
        for flow in nPath:
            while len(nPath[flow]) != path_number:
                if len(nPath[flow]) < path_number:
                    nPath[flow].append(nPath[flow][0])
                if len(nPath) > path_number:
                    nPath[flow].pop()
        edge_info = self.path_to_link_vector(nPath)
        self.logger.info('edge_info: %s', str(edge_info))
        flows = nPath.keys()
        self.logger.info('candidate flows: %s', str(flows))
        if mode == 'MILP':
            flows, flow_require = max_admittable_flow(res_bw, flows, edge_info, path_number, flow_require)
            self.logger.info('admittable flow: %s', str(flow_require))
            chosen_path_info, obj = milp_sdn_routing(res_bw, flows, edge_info, path_number, flow_require)
        elif mode == 'NSGA2':
            nm = NetModel(res_bw, flows, edge_info, path_number, flow_require)
            chosen_path_info, obj = nm.main()
        self.logger.info('the minimize maximize link utilization: %s', str(obj))
        return chosen_path_info, nPath


    def path_to_link_vector(self, npath):
        '''
            given a set of path, transform it to a link vector
        '''
        edges_info = deepcopy(self.awareness.edges)
        for flow in npath:
            for j, path in enumerate(npath[flow]):
                for i in xrange(len(path) - 1):
                    if (path[i], path[i + 1]) in edges_info:
                        edges_info[(path[i], path[i + 1])][flow][j] = 1
                    elif (path[i+1], path[i]) in edges_info:
                        edges_info[(path[i + 1], path[i])][flow][j] = 1
        return edges_info

    def ilp_data_handle(self, ip_pkt, eth_type, datapath_id, require_band):
        '''
           generating the data for ilp module
        '''
        # avoid reverse path packet-in packet to controller
        if (ip_pkt.dst, ip_pkt.src) not in self.flow_path:
            if (ip_pkt.src, ip_pkt.dst) not in self.flow_path:
                in_port = self.get_port(ip_pkt.src, self.awareness.access_table)
                self.logger.info("ilpdata ip_src: %s,ip_dst: %s,in_port: %s" % (ip_pkt.src, ip_pkt.dst, in_port))
                self.logger.info("count:%s" % self.count)
                self.handle_flag = 1   # this is new QoS flow, can handle with ilp module

                result = self.get_sw(datapath_id, in_port, ip_pkt.src, ip_pkt.dst)
                flow_info = []
                flow_info.append(require_band)
                # flow_info.append(setting.priority_weight[ip_pkt.src])
                flow_info.append(0)
                flow_info.append((result[0], result[1]))
                # (eth_type, ip_pkt.src, ip_pkt.dst, in_port)--> [require_band,priority,(src_dp,dst_dp)]
                self.flow[(eth_type, ip_pkt.src, ip_pkt.dst, in_port)] = flow_info
                self.flow_path[(ip_pkt.src, ip_pkt.dst)] = [result]
                #  self.flow_path[(eth_type, ip_pkt.src, ip_pkt.dst, in_port)] = [result]
                # (src,dst) --> (eth_type, ip_pkt.src, ip_pkt.dst, in_port)
                self.lookup[(ip_pkt.src, ip_pkt.dst)] = (eth_type, ip_pkt.src, ip_pkt.dst, in_port)
                self.show_ilp_data()
                self.count += 1  # flow identification
                # assert self.count < 10
