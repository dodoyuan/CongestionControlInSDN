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

from __future__ import division
import copy
from operator import attrgetter
from ryu import cfg
from ryu.base import app_manager
from ryu.base.app_manager import lookup_service_brick
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub
from ryu.lib.packet import packet
import setting
from collections import defaultdict


class NetworkMonitor(app_manager.RyuApp):
    """
        NetworkMonitor is a Ryu app for collecting traffic information.

    """
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(NetworkMonitor, self).__init__(*args, **kwargs)
        self.name = 'monitor'
        self.datapaths = {}
        self.port_stats = {}
        self.port_speed = {}
        # self.flow_stats = {}
        # self.flow_speed = {}
        self.stats = {}
        self.free_bandwidth = {}

        self.awareness = lookup_service_brick('awareness')
        self.graph = None
        self.congest_link = (0, 0)
        # Start to green thread to monitor traffic and calculating
        # free bandwidth of links respectively.
        self.monitor_thread = hub.spawn(self._monitor)
        self.save_freebandwidth_thread = hub.spawn(self._save_bw_graph)
        # note the allocated bandwidth
        self.res_bw = {}
        self.one_shot = True

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        """
            Record datapath's info
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

    def _monitor(self):
        """
            Main entry method of monitoring traffic.
        """
        while setting.WEIGHT == 'bw' and setting.prob_bandwidth:
            self.stats['port'] = {}
            for dp in self.datapaths.values():
                self._request_stats(dp)

            hub.sleep(setting.MONITOR_PERIOD)
            if self.stats['port']:
                self.show_stat('port')
                hub.sleep(1)

        hub.sleep(setting.MONITOR_PERIOD)
        if self.one_shot:
            for edge in self.awareness.edges.keys():
                    self.res_bw[edge] = setting.get_bandwidth(edge)
            print 'res bw:', self.res_bw
            self.one_shot = False

    def _save_bw_graph(self):
        """
            Save bandwidth data into networkx graph object.
        """
        while setting.WEIGHT == 'bw' and setting.prob_bandwidth:
            self.graph = self.create_bw_graph(self.free_bandwidth)
            self.logger.debug("save_freebandwidth")
            hub.sleep(setting.MONITOR_PERIOD)

    def _request_stats(self, datapath):
        """
            Sending request msg to datapath
        """
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    def get_min_bw_of_links(self, path, min_bw):
        """
            Getting bandwidth of path. Actually, the mininum bandwidth
            of links is the bandwidth, because it is the neck bottle of path.
        """
        _len = len(path)
        if _len > 1:
            minimal_band_width = min_bw
            for i in xrange(_len-1):
                if setting.prob_bandwidth:   # work for prob
                    pre, curr = path[i], path[i+1]
                    if 'bandwidth' in self.graph[pre][curr]:
                        bw = self.graph[pre][curr]['bandwidth']
                        minimal_band_width = min(bw, minimal_band_width)
                    else:
                        continue
                else:                        # work for making note
                    if (path[i], path[i+1]) in self.res_bw:
                        bw = self.res_bw[(path[i], path[i+1])]
                        minimal_band_width = min(bw, minimal_band_width)
                    elif (path[i+1], path[i]) in self.res_bw:
                        bw = self.res_bw[(path[i], path[i + 1])]
                        minimal_band_width = min(bw, minimal_band_width)
            return minimal_band_width
        return min_bw

    def get_bw_guaranteed_path(self, paths, require_band):
        """
            Get best path by comparing paths.
            return a path with the guaranteed band-with
            WSP algorithm
        """
        reconf_flag = 1
        # max_bw_of_paths = 0
        bw_guaranteed_paths = paths[0]
        # for path in paths:
        #     # self.logger.info("fun get bw guaranteed path:%s" % path)
        #     min_bw = setting.MAX_CAPACITY
        #     min_bw = self.get_min_bw_of_links(path, min_bw)
        #     if min_bw > max_bw_of_paths:
        #         max_bw_of_paths = min_bw
        #         if min_bw > require_band:
        #             reconf_flag = 0
        #             return path, reconf_flag
        #         bw_guaranteed_paths = path
        # ------------------WSP-----------------------
        # for path in paths:
        #     # self.logger.info("fun get bw guaranteed path:%s" % path)
        #     min_bw = setting.MAX_CAPACITY
        #     min_bw = self.get_min_bw_of_links(path, min_bw)
        #     if min_bw > max_bw_of_paths:
        #         max_bw_of_paths = min_bw
        #         bw_guaranteed_paths = path
        # ---------------------------------------------
        # shortest path
        # max_bw_of_paths = self.get_min_bw_of_links(bw_guaranteed_paths, setting.MAX_CAPACITY)
        # ---------------------------------------------
        return bw_guaranteed_paths

    def res_bw_show(self):
        print '--------------------residual bandwidth------------------'
        for edge, value in self.res_bw.items():
            print edge, '----->', value
        print '------------------------end-----------------------------'

    def update_res_bw_and_congestion_detect(self, path, require_band):
        # update the residual bandwidth
        reconf_flag = 1
        min_bw, congstion_edge = self.update_res_bw(path, require_band)
        self.logger.info('min_bw: %s congstion_edge: %s', min_bw, congstion_edge)
        self.res_bw_show()
        # the link congestion threshold is 0.9
        if min_bw / setting.MAX_CAPACITY > 0.11:
            reconf_flag = 0
        else:
            # function for detecting the congesting link
            # s1, s2 = self.dectect_congest_link(bw_guaranteed_paths)
            self.congest_link = [congstion_edge, min_bw]
        return reconf_flag

    def update_res_bw(self, path, require_bd):
        '''
           given a path and required bandwidth, update the allocated bandwidth.
           :return the minimal bandwidth of links
           update bandwidth with minus require_bd
        '''
        _len, edge = len(path), None
        min_bw = setting.MAX_CAPACITY
        if _len > 1:
            for i in xrange(_len - 1):
                if (path[i], path[i+1]) in self.res_bw:
                    self.res_bw[(path[i], path[i+1])] = max(self.res_bw[(path[i], path[i+1])] - require_bd, 0)
                    if self.res_bw[(path[i], path[i+1])] < min_bw:
                        min_bw, edge = self.res_bw[(path[i], path[i+1])], (path[i], path[i+1])
                elif (path[i+1], path[i]) in self.res_bw:
                    self.res_bw[(path[i+1], path[i])] = max(self.res_bw[(path[i+1], path[i])] - require_bd, 0)
                    if self.res_bw[(path[i+1], path[i])] < min_bw:
                        min_bw, edge = self.res_bw[(path[i+1], path[i])], (path[i+1], path[i])
            return min_bw, edge
        else:
            return setting.MAX_CAPACITY, edge


    def dectect_congest_link(self,path):
        '''
           if the path just one hop, as len(path)=1
        '''
        _len = len(path)
        s1, s2 = 0, 0
        if _len > 1:
            minimal_band_width = setting.MAX_CAPACITY
            for i in xrange(_len - 1):
                pre, curr = path[i], path[i + 1]
                if 'bandwidth' in self.graph[pre][curr]:
                    bw = self.graph[pre][curr]['bandwidth']
                    # minimal_band_width = min(bw, minimal_band_width)
                    if bw < minimal_band_width:
                        s1, s2 = pre, curr
                        minimal_band_width = bw
                else:
                    continue
            return s1, s2
        # TODO: single hop link
        return path[0], path[0]

    def residual_bandwidth(self, choose_flow):
        '''
           get the residual bandwidth of the graph
           and remove of the chosen flow
            update bandwidth with add require_bd
        '''
        # edge_bw = self.awareness.edges
        # for src_sw, dst_sw in edge_bw:
        #     self.res_bw[src_sw][dst_sw] = self.graph[src_sw][dst_sw]['bandwidth']
        for value in choose_flow:
            path = value[1]
            for i in xrange(len(path)-1):
                if (path[i], path[i + 1]) in self.res_bw:
                    self.res_bw[(path[i], path[i + 1])] += value[2]
                    if self.res_bw[(path[i], path[i + 1])] > setting.MAX_CAPACITY:
                        self.res_bw[(path[i], path[i + 1])] = setting.MAX_CAPACITY
                elif (path[i+1], path[i]) in self.res_bw:
                    self.res_bw[(path[i+1], path[i])] += value[2]
                    if self.res_bw[(path[i+1], path[i])] > setting.MAX_CAPACITY:
                        self.res_bw[(path[i+1], path[i])] = setting.MAX_CAPACITY
        # return self.res_bw

    def create_bw_graph(self, bw_dict):
        """
            Save bandwidth data into networkx graph object.
        """
        try:
            graph = self.awareness.graph
            link_to_port = self.awareness.link_to_port
            for link in link_to_port:
                (src_dpid, dst_dpid) = link
                (src_port, dst_port) = link_to_port[link]
                if src_dpid in bw_dict and dst_dpid in bw_dict:
                    bw_src = bw_dict[src_dpid][src_port]
                    bw_dst = bw_dict[dst_dpid][dst_port]
                    bandwidth = min(bw_src, bw_dst)
                    # add key:value of bandwidth into graph.
                    graph[src_dpid][dst_dpid]['bandwidth'] = bandwidth
                else:
                    graph[src_dpid][dst_dpid]['bandwidth'] = 0
            return graph
        except:
            self.logger.info("Create bw graph exception")
            if self.awareness is None:
                self.awareness = lookup_service_brick('awareness')
            return self.awareness.graph

    def _save_freebandwidth(self, dpid, port_no, speed):
        # Calculate free bandwidth of port and save it.
        # port_state = self.port_features.get(dpid).get(port_no)
        #
        port_state = 1  # TODO creat map with port status
        if port_state:
            # get link capacity from map of each link capacity
            capacity = setting.get_link_capacity(dpid, port_no, 0)
            # bandwidth Mbps
            curr_bw = self._get_free_bw(capacity, speed)
            self.free_bandwidth[dpid].setdefault(port_no, None)
            self.free_bandwidth[dpid][port_no] = curr_bw
        else:
            self.logger.info("Fail in getting port state")

    def _save_stats(self, _dict, key, value, length):
        if key not in _dict:
            _dict[key] = []
        _dict[key].append(value)

        if len(_dict[key]) > length:
            _dict[key].pop(0)

    def _get_speed(self, now, pre, period):
        if period:
            return (now - pre) / (period)
        else:
            return 0

    def _get_free_bw(self, capacity, speed):
        # BW:Mbit/s
        return max(capacity - float(speed * 8) / 10**6, 0)

    def _get_time(self, sec, nsec):
        return sec + nsec / (10 ** 9)

    def _get_period(self, n_sec, n_nsec, p_sec, p_nsec):
        return self._get_time(n_sec, n_nsec) - self._get_time(p_sec, p_nsec)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        """
            Save port's stats info
            Calculate port's speed and save it.
        """
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        self.stats['port'][dpid] = body
        self.free_bandwidth.setdefault(dpid, {})

        for stat in sorted(body, key=attrgetter('port_no')):
            port_no = stat.port_no
            if port_no != ofproto_v1_3.OFPP_LOCAL:
                key = (dpid, port_no)
                value = (stat.tx_bytes, stat.rx_bytes, stat.rx_errors,
                         stat.duration_sec, stat.duration_nsec)

                self._save_stats(self.port_stats, key, value, 5)

                # Get port speed.
                pre = 0
                period = setting.MONITOR_PERIOD
                tmp = self.port_stats[key]
                if len(tmp) > 1:
                    pre = tmp[-2][0] + tmp[-2][1]
                    period = self._get_period(tmp[-1][3], tmp[-1][4],
                                              tmp[-2][3], tmp[-2][4])

                speed = self._get_speed(
                    self.port_stats[key][-1][0] + self.port_stats[key][-1][1],
                    pre, period)

                self._save_stats(self.port_speed, key, speed, 5)
                self._save_freebandwidth(dpid, port_no, speed)

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _port_status_handler(self, ev):
        """
            Handle the port status changed event.
        """
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no
        dpid = msg.datapath.id
        ofproto = msg.datapath.ofproto

        reason_dict = {ofproto.OFPPR_ADD: "added",
                       ofproto.OFPPR_DELETE: "deleted",
                       ofproto.OFPPR_MODIFY: "modified", }

        if reason in reason_dict:
            print "switch%d: port %s %s" % (dpid, reason_dict[reason], port_no)
        else:
            print "switch%d: Illeagal port state %s %s" % (port_no, reason)

    def show_stat(self, type):
        '''
            Show statistics info according to data type.
            type: 'port' 'flow'
        '''
        if setting.TOSHOW is False:
            return

        bodys = self.stats[type]
        if(type == 'flow'):
            print('datapath    ''     in-port    ip-dst   '
                  'out-port packets  bytes  flow-speed(B/s)')
            print('--------------- ''  -------- ----------- '
                  '-------- ----- - ------- -----------')
            for dpid in bodys.keys():
                for stat in sorted(
                    [flow for flow in bodys[dpid] if flow.priority == 1],
                    key=lambda flow: (flow.match.get('in_port'),
                                      flow.match.get('ipv4_dst'))):
                    print('%016x %8x %17s %8x %8d %8d %8.1f' % (
                        dpid,
                        stat.match['in_port'], stat.match['ipv4_dst'],
                        stat.instructions[0].actions[0].port,
                        stat.packet_count, stat.byte_count,
                        abs(self.flow_speed[dpid][
                            (stat.match.get('in_port'),
                            stat.match.get('ipv4_dst'),
                            stat.instructions[0].actions[0].port)][-1])))
            print '\n'

        if(type == 'port'):
            print('datapath          port   ''rx-bytes '
                  'tx-bytes port-speed(B/s)'
                  ' free-bandwidth(Mbps)  '
                  )
            print('--------------   -------- ''------ '
                  '-------- -------- '
                  '----------   ')
            format = '%016x %8x %8d %8d %8.1f %8.4f'
            for dpid in bodys.keys():
                for stat in sorted(bodys[dpid], key=attrgetter('port_no')):
                    if stat.port_no != ofproto_v1_3.OFPP_LOCAL:
                        print(format % (
                            dpid, stat.port_no,
                            stat.rx_bytes,
                            stat.tx_bytes,
                            abs(self.port_speed[(dpid, stat.port_no)][-1]),
                            self.free_bandwidth[dpid][stat.port_no]))
            print '\n'
