#! /usr/bin/env python
# --*--coding:utf-8--*--

# Copyright (C) 2017 Yuan qijie at Beijing University of Posts
# and Telecommunications.
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
# https://github.com/dodoyuan/SDN-QoS-RYU-APP.git
# import setting
import pulp
from collections import defaultdict
import time

def exeTime(func):
    def newFunc(*args, **args2):
        t0 = time.time()
        print "@%s, {%s} start" % (time.strftime("%X", time.localtime()), func.__name__)
        back = func(*args, **args2)
        print "@%s, {%s} end" % (time.strftime("%X", time.localtime()), func.__name__)
        print "@%.3fs taken for {%s}" % (time.time() - t0, func.__name__)
        return back
    return newFunc



@exeTime
def milp_sdn_routing(res_bw, flows, edge_info, path_num, flow_require):
    '''
    this function is used for reroute the chosen flows
    '''
    edges = edge_info.keys()

    model = pulp.LpProblem("link load balance", pulp.LpMinimize)
    y = pulp.LpVariable.dicts("choose a path", [(flow, path_index) for flow in flows
            for path_index in xrange(path_num)], 0, 1, cat='Binary')
    z = pulp.LpVariable('z', lowBound=0, cat='Continuous')

    # constrains 1
    for flow in flows:
        model += pulp.lpSum(y[(flow, i)] for i in xrange(path_num)) == 1

    # constrains 2
    total_used_bd = {}
    for edge in edges:
        total_used_bd[edge] = 0
        for flow in flows:
            total_used_bd[edge] += sum(flow_require[flow] * y[(flow, i)] *
                                       edge_info[edge][flow][i] for i in xrange(path_num))

        model += total_used_bd[edge] <= res_bw[edge]
        used_bd = 10 - (res_bw[edge] - total_used_bd[edge])
        model += z >= used_bd

    # objection
    model += z, 'minimize the link cost'

    model.solve()
    status = pulp.LpStatus[model.status]
    print status

    total_cost = pulp.value(model.objective)
    print "the minimize cost is {}".format(total_cost)

    chosen_path = {}
    for v in model.variables():
        if v.varValue and 'path' in v.name:
            print v.name, '=', v.varValue
            temp = v.name.split(',')
            src, dst = temp[0][-9:-1], temp[1][2:-2]
            chosen_path[(src, dst)] = temp[2][1]
    # print flows
    # print chosen_path
    return chosen_path, total_cost

def max_admittable_flow(res_bw, flows, edge_info, path_num, flow_require):
    '''
        this function is used to calculate the max admittable flow
    '''
    edges = edge_info.keys()

    model = pulp.LpProblem("max admittable flow", pulp.LpMaximize)
    y = pulp.LpVariable.dicts("choose a path", [(flow, path_index) for flow in flows
                                                for path_index in xrange(path_num)], 0, 1, cat='Binary')
    z = pulp.LpVariable.dicts('hand the flow or not', flows, 0, 1, cat='Binary')


    # constrains 1
    for flow in flows:
        model += pulp.lpSum(y[(flow, i)] for i in xrange(path_num)) == z[flow]

    # constrains 2
    total_used_bd = {}
    for edge in edges:
        total_used_bd[edge] = 0
        for flow in flows:
            total_used_bd[edge] += sum(flow_require[flow] * y[(flow, i)] *
                                       edge_info[edge][flow][i] for i in xrange(path_num))

        model += total_used_bd[edge] <= res_bw[edge]

    # objection
    model += pulp.lpSum(flow_require[flow] * z[flow] for flow in flows), 'max the admittable flow'

    model.solve()
    status = pulp.LpStatus[model.status]
    print status

    total_amittable = pulp.value(model.objective)
    print "the max admittable flow is {}".format(total_amittable)
    for v in model.variables():
        if v.varValue and 'hand' in v.name:
            print v.name, '=', v.varValue


def link_cost(bandwidth):
    '''
       correspond to the piecewise function
    '''
    if 0 <= bandwidth < 10.0/3:
        return bandwidth
    elif 10.0/3 <= bandwidth < 20.0/3:
        return 3 * bandwidth
    elif 20.0/3 <= bandwidth < 9:
        return 10 * bandwidth - 160.0/3
    elif 9 <= bandwidth < 10:
        return 70 * bandwidth - 1780.0/3
    else:
        return 700


def neighbor_head(node, edges):
    # return all the linked neighbors of node node
    linked_edges = []
    for e in edges:
        if node == e[1]:
            linked_edges.append(e)
    return linked_edges


def neighbor_tail(node, edges):
    # return all the linked neighbors of node node
    linked_edges = []
    for e in edges:
        if node == e[0]:
            linked_edges.append(e)
    return linked_edges

@exeTime
def milp_constrains(nodes, edges, r, p, flow, capacity, src_dst):
    '''

    :param nodes: []
    :param edges: [()]
    :param r: []
    :param p: []
    :param flow:[0,1,2]
    :param capacity: int
    :param src_dst: [()]
    :return:
    '''
    s, d = gene_matrix(nodes, src_dst)
    model = pulp.LpProblem("suitable path for higher priority", pulp.LpMaximize)
    y = pulp.LpVariable.dicts("handle this flow or not", flow, 0, 1, cat='Binary')
    u = pulp.LpVariable.dicts("selected path of flow", [(f, edge) for f in flow for edge in edges], 0, 1, cat='Binary')

    # objective function
    model += pulp.lpSum(p[i] * y[i] for i in flow), "shortest path with suitable controllers placement"

    # flow constrain
    for n in flow:      # traverse every node
        for m in nodes:  # arbitrarily intermediate node
            model += pulp.lpSum(u[(n, edge)] for edge in neighbor_head(m, edges)) - \
                     pulp.lpSum(u[(n, edge)] for edge in neighbor_tail(m, edges)) == (d[n][m] - s[n][m]) * y[n]
            # model += pulp.lpSum(u[(n, edge)] for edge in neighbor_head(m)) + \
            #          pulp.lpSum(u[(n, edge)] for edge in neighbor_tail(m)) <= 1

    for edge in edges:
        model += pulp.lpSum(r[n] * u[(n, edge)] for n in flow) <= capacity[edge]

    for n in flow:
        for edge in edges:
            model += u[(n, edge)] <= y[n]

    model.solve()
    status = pulp.LpStatus[model.status]
    print status

    max_priority = pulp.value(model.objective)
    # print "the max priority is {}".format(max_priority)

    path = defaultdict(dict)
    for v in model.variables():
        if v.varValue:
            # print v.name, '=', v.varValue
            # selected_path_of_flow_(1,_(1,_5))
            if 'path' in v.name:
                temp = v.name.split('_')
                flow_number = int(temp[4][-2])
                link_src, link_dst = int(temp[5][-2]), int(temp[6][-3])
                path[flow_number][link_src] = link_dst
    # print path
    #  {1: {1: 5, 5: 6, 6: 7, 7: 8}, 2: {1: 2, 2: 3, 3: 4, 4: 8}}
    path = path_extr(src_dst, path)
    return path, max_priority


def path_extr(src_dst,path):
    '''
       {1: {1: 5, 5: 6, 6: 7, 7: 8}, 2: {1: 2, 2: 3, 3: 4, 4: 8}} --> {1:[1,5,6,7,8]}
    '''
    path_changed = defaultdict(list)
    for flow in path.keys():
        src, dst = src_dst[flow][0], src_dst[flow][1]
        current = src
        while current != dst:
            path_changed[flow].append(current)
            current = path[flow][current]
        path_changed[flow].append(dst)
    return path_changed


def gene_matrix(nodes, src_dst):
    source_matrix = defaultdict(lambda: [0 for _ in range(len(nodes) + 1)])
    des_matrix = defaultdict(lambda: [0 for _ in range(len(nodes) + 1)])
    for key, value in enumerate(src_dst, 0):
        source_matrix[key][value[0]] = 1
        des_matrix[key][value[1]] = 1
    return source_matrix, des_matrix


# milp_constrains function testcase

# if __name__ == '__main__':
#
#     print 'hope god help '
#     # predefined data
#     nodes = [1, 2, 3, 4, 5, 6, 7, 8]
#     edges = [(1, 2), (2, 3), (3, 4), (4, 8), (1, 5), (5, 4), (5, 6), (6, 7), (7, 8),
#              (2, 1), (3, 2), (4, 3), (8, 4), (5, 1), (4, 5), (6, 5), (7, 6), (8, 7)]
#     r = [0, 5, 5, 2]
#
#     p = [0, 4, 2, 1]
#     flow = [1, 2, 3]
#     capacity = 5
#     src_dst = {1: (1, 8), 2: (1, 8), 3: (6, 7)}
#     milp_constrains(nodes, edges, r, p, flow, capacity, src_dst)

if __name__ == '__main__':
    # milp_sdn_routing(res_bw, flows, edge_info, path_num, flow_require):
    res_bw = {(1, 2): 3, (1, 3): 3, (1, 4): 3, (2, 5): 3, (3, 7): 3, (4, 6): 3,
               (5, 7): 3, (6, 7): 3}
    flows = [('10.0.0.1','10.0.0.4'), ('10.0.0.2', '10.0.0.5'), ('10.0.0.3','10.0.0.6')]
    path_num = 3
    flow_require = {('10.0.0.1','10.0.0.4'): 4, ('10.0.0.2', '10.0.0.5'): 1.5, ('10.0.0.3', '10.0.0.6'): 1.5}
    edge_info = {
        (1, 2): {('10.0.0.1', '10.0.0.4'): {0: 1, 1: 0, 2: 0}, ('10.0.0.2', '10.0.0.5'): {0: 1, 1: 0, 2: 0},
                 ('10.0.0.3', '10.0.0.6'): {0: 1, 1: 0, 2: 0}},
        (2, 5): {('10.0.0.1', '10.0.0.4'): {0: 1, 1: 0, 2: 0}, ('10.0.0.2', '10.0.0.5'): {0: 1, 1: 0, 2: 0},
                 ('10.0.0.3', '10.0.0.6'): {0: 1, 1: 0, 2: 0}},
        (5, 7): {('10.0.0.1', '10.0.0.4'): {0: 1, 1: 0, 2: 0}, ('10.0.0.2', '10.0.0.5'): {0: 1, 1: 0, 2: 0},
                 ('10.0.0.3', '10.0.0.6'): {0: 1, 1: 0, 2: 0}},
        (1, 3): {('10.0.0.1', '10.0.0.4'): {0: 0, 1: 1, 2: 0}, ('10.0.0.2', '10.0.0.5'): {0: 0, 1: 1, 2: 0},
                 ('10.0.0.3', '10.0.0.6'): {0: 0, 1: 1, 2: 0}},
        (3, 7): {('10.0.0.1', '10.0.0.4'): {0: 0, 1: 1, 2: 0}, ('10.0.0.2', '10.0.0.5'): {0: 0, 1: 1, 2: 0},
                 ('10.0.0.3', '10.0.0.6'): {0: 0, 1: 1, 2: 0}},
        (1, 4): {('10.0.0.1', '10.0.0.4'): {0: 0, 1: 0, 2: 1}, ('10.0.0.2', '10.0.0.5'): {0: 0, 1: 0, 2: 1},
                 ('10.0.0.3', '10.0.0.6'): {0: 0, 1: 0, 2: 1}},
        (4, 6): {('10.0.0.1', '10.0.0.4'): {0: 0, 1: 0, 2: 1}, ('10.0.0.2', '10.0.0.5'): {0: 0, 1: 0, 2: 1},
                 ('10.0.0.3', '10.0.0.6'): {0: 0, 1: 0, 2: 1}},
        (6, 7): {('10.0.0.1', '10.0.0.4'): {0: 0, 1: 0, 2: 1}, ('10.0.0.2', '10.0.0.5'): {0: 0, 1: 0, 2: 1},
                 ('10.0.0.3', '10.0.0.6'): {0: 0, 1: 0, 2: 1}},
    }

    max_admittable_flow(res_bw, flows, edge_info, path_num, flow_require)

    # print edge_info[(1,2)][('10.0.0.1','10.0.0.4')][1]

    # print int(link_cost(10))
    # print int(link_cost(8))
    #
    # used_bd = 8
    # a = used_bd if 0 <= used_bd < 10.0 / 3 else 3 * used_bd if 10.0 / 3 <= used_bd < 20.0 / 3 \
    #     else 10 * used_bd - 160.0 / 3 if 20.0 / 3 <= used_bd < 9 else 70 * used_bd - 1780.0 / 3 if \
    #     9 <= used_bd < 10 else 700
    # print a

