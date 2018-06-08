# --*-- coding:utf8 --*--

'''
@summary: Implementation of the NSGA-II algorithm in Python.
@version: 1.1
@since: 2018-06
@author: Yuan qijie
@contact: yuan_bupt@163.com
@copyright: Copyright 2018 Yuan Qijie
'''



class NetModel:
    '''
    用来实现多目标优化的数据建模。输入数据格式如下：
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
    '''
    def __init__(self, res_bw, flows, edge_info, path_number, flow_require):
        self.res_bw = res_bw
        self.flows = flows
        self.edge_info = edge_info
        self.path_number = path_number
        self.flow_require_dict = flow_require

    def objective_function1(self, solution):
        '''
        function to get the total accept flow bandwidth
        :param solution: [state1, state2,...,stateN]
        :return: the total flow throughput
        '''
        accept_flow_bandwith = 0
        for i, state in enumerate(solution):
            if state:
                accept_flow_bandwith += self.flow_require_dict[self.flows[i]]
        return -accept_flow_bandwith

    def objective_function2(self, solution):
        '''
        function to get the max bandwidth use ration。返回的是最大的链路利用率。
        :param solution: [state1, state2,...,stateN]
        :return:  the max bandwidth use ration
        ATTENTION：
           为了简化处理，固定住每条链路带宽为10M，返回的不是最大的链路利用率，而是最大的
           链路使用带宽。
        '''
        assert len(solution) == len(self.flows)
        edges = self.edge_info.keys()
        max_used_bandwidth = 0
        for edge in edges:
            total_used_bd = 10 - self.res_bw[edge]
            for i, flow in enumerate(self.flows):
                if solution[i]:
                    total_used_bd += self.flow_require_dict[flow] * self.edge_info[edge][flow][solution[i] - 1]
            if total_used_bd > max_used_bandwidth:
                max_used_bandwidth = total_used_bd
        return max_used_bandwidth

    def solution_is_validate(self, solution):
        '''
        function to determine the solution is valitate. 需要保证每一条链路承载的数据
        流大小不超过链路带宽。
        :param solution: [state1, state2,...,stateN]
        :return: True or False
        edge_info = {
        (1, 2): {('10.0.0.1', '10.0.0.4'): {0: 1, 1: 0, 2: 0} ...}
        '''
        assert len(solution) == len(self.flows)
        edges = self.edge_info.keys()
        for edge in edges:
            need_use_bd = 0
            for i, flow in enumerate(self.flows):
                if solution[i]:
                    need_use_bd += self.flow_require_dict[flow] * self.edge_info[edge][flow][solution[i]-1]
            if need_use_bd > self.res_bw[edge]:
                return False
        return True