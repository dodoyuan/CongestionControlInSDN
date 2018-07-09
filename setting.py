
#  coding:utf8
#  Common Setting for Network awareness module.

from collections import defaultdict

DISCOVERY_PERIOD = 15  # For discovering topology.

MONITOR_PERIOD = 3  # For monitoring traffic

DELAY_DETECTING_PERIOD = 2  # For detecting link delay.

TOSHOW = False  # For showing information in terminal

# TODO：应该是一个矩阵
MAX_CAPACITY = 3  # Max capacity of link

path_number = 3

# we have two model, when pro_bandwidth is true, means it will automatically
# update the bandwidth record according to the prob action. And when
# is false, it means it just record and update.
prob_bandwidth = False

# There have two choses: MILP & NSGA2 to handle network congestion
mode = 'NSGA2'


def get_link_capacity(dpid, port, return_matrix_flag):
    link_capacity = defaultdict(lambda: defaultdict(lambda: 10))
    # link_capacity[4][1] = 100
    # link_capacity[4][2] = 100
    # link_capacity[4][3] = 100
    # link_capacity[4][4] = 100
    # link_capacity[1][1] = 100
    # link_capacity[1][2] = 100
    # link_capacity[1][3] = 100
    # link_capacity[1][4] = 100
    if return_matrix_flag:
        return link_capacity
    else:
        return link_capacity[dpid][port]

k_paths = 2

WEIGHT = 'bw'

# predefined requirement band-with of each source IP
require_band = {"10.0.0.1": 2, "10.0.0.2": 2, "10.0.0.3": 2, "10.0.0.4": 2}

# predefined priority of each source IP
priority_weight = {"10.0.0.1": 16, "10.0.0.2": 8, "10.0.0.3": 4}


# self-defined the residual bandwidth of each edge
# def get_bandwidth(edge):
#     if edge == (1, 2) or edge == (2, 1):
#         return 4.3
#     if edge == (2, 3) or edge == (3, 2):
#         return 3.9
#     if edge == (3, 4) or edge == (4, 3):
#         return 4.8
#     if edge == (4, 6) or edge == (6, 4):
#         return 5.5
#     if edge == (1, 5) or edge == (5, 1):
#         return 5.9
#     if edge == (5, 6) or edge == (6, 5):
#         return 5.8
#     if edge == (6, 7) or edge == (7, 6):
#         return 5.5
#     if edge == (1, 8) or edge == (8, 1):
#         return 5.1
#     if edge == (8, 9) or edge == (9, 8):
#         return 5.3
#     if edge == (9, 6) or edge == (6, 9):
#         return 4.1
#     if edge == (2, 5) or edge == (5, 2):
#         return 5.0

def get_bandwidth(edge):
    return 3
