# --*-- coding:utf8 --*--

'''
@summary: Implementation of the NSGA-II algorithm in Python.
@version: 1.1
@since: 2018-06
@author: Yuan qijie
@contact: yuan_bupt@163.com
@copyright: Copyright 2018 Yuan Qijie
'''
from nsga2Lib import Solution
from nsga2Lib import NSGAII
import random


class T1Solution(Solution):
    '''
    Solution for the T1 function.
    '''

    def __init__(self, flows_num, path_num):
        '''
        Constructor.
        '''
        Solution.__init__(self, 2)
        # 生成的初始解,为每条数据流随机选择一条路径
        self.flows_num = flows_num
        self.path_num = path_num
        self.attributes = self.generate_new_solution()
        self.evaluate_solution()

    def generate_new_solution(self):
        '''
        生成一个解空间，确保该解有效，即分配的流量不超过承载的带宽。
        TODO：如何有效生成一个解
        '''
        while True:
            temp_solution = []
            for _ in range(self.flows_num):
                temp_solution.append(random.randint(0, self.path_num))
            if netmodel.solution_is_validate(temp_solution):
                return temp_solution

    def evaluate_solution(self):
        '''
        Implementation of method evaluate_solution() for T1 function.
        '''
        self.objectives[0] = netmodel.objective_function1(self.attributes)
        self.objectives[1] = netmodel.objective_function2(self.attributes)

    def crossover(self, other):
        '''
        Crossover of T1 solutions.
        '''
        child_solution = T1Solution(self.flows_num, self.path_num)
        # for i in range(30):
        #     child_solution.attributes[i] = math.sqrt(self.attributes[i] * other.attributes[i])
        point = random.randint(0, self.flows_num - 1)
        attributes = self.attributes[:point] + other.attributes[point:]
        if netmodel.solution_is_validate(attributes):
            child_solution.attributes = attributes
        else:
            child_solution.attributes = self.generate_new_solution()
        return child_solution

    def mutate(self):
        '''
        Mutation of T1 solution.
        '''
        round = 10
        while round:
            attr = self.attributes[:]
            attr[random.randint(0, self.flows_num-1)] = random.randint(0, self.path_num)
            if netmodel.solution_is_validate(attr):
                self.attributes = attr
                return
            round -= 1
        print('mutate failure')


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
        self.flow_num = len(flows)

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

    def main(self):
        nsga2 = NSGAII(2, 0.1, 1.0)
        P = []
        # 初始化种群数量
        for i in range(70):
            P.append(T1Solution(self.flow_num, self.path_number))

        # 迭代次数 30，种群大小 70
        nsga2.run(P, 70, 30)

        csv_file = open('nsga2_out.csv', 'w')
        csv_file.write('----------- front 最优解 ---------\n')

        # 遍历所有的解空间，找出第一个优化目标最小的解
        accept_bandwidth = float('inf')
        chosen_path_info = []
        max_used_bandwidth = 0
        for i in range(len(P)):
            print(P[i].attributes)
            if P[i].objectives[0] < accept_bandwidth:
                accept_bandwidth = P[i].objectives[0]
                max_used_bandwidth = P[i].objectives[1]
                chosen_path_info = P[i].attributes
            csv_file.write("" + str(P[i].objectives[0]) + ", " + str(P[i].objectives[1]) + "\n")
        csv_file.close()

        # 构造符合目标的返回数据格式
        chosen_path_dict = {}
        for i, path_index in enumerate(chosen_path_info):
            if path_index:
                chosen_path_dict[(self.flows[i])] = path_index - 1
        return chosen_path_dict, max_used_bandwidth


if __name__ == '__main__':
    res_bw = {(1, 2): 3, (1, 3): 3, (1, 4): 3, (2, 5): 3, (3, 7): 3, (4, 6): 3,
              (5, 7): 3, (6, 7): 3}
    flows = [('10.0.0.1', '10.0.0.4'), ('10.0.0.2', '10.0.0.5'), ('10.0.0.3', '10.0.0.6')]
    path_num = 3
    flow_require = {('10.0.0.1', '10.0.0.4'): 2, ('10.0.0.2', '10.0.0.5'): 2, ('10.0.0.3', '10.0.0.6'): 2}
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

    # res_bw = {(1, 2): 4.3, (2, 3): 2.9, (3, 4): 4.8, (4, 6): 3, (1, 5): 5.9, (5, 6): 7.5,
    #           (6, 7): 5.5, (1, 8): 3.1, (8, 9): 5.3, (9, 10): 4.1, (2, 5): 5}
    # flows = [('10.0.0.1', '10.0.0.5'), ('10.0.0.2', '10.0.0.6'), ('10.0.0.3', '10.0.0.7'),  ('10.0.0.4', '10.0.0.8')]
    # path_num = 3
    # flows_num = len(flows)
    # flow_require = {('10.0.0.1', '10.0.0.5'): 2.1, ('10.0.0.2', '10.0.0.6'): 0.6,
    #                 ('10.0.0.3', '10.0.0.7'): 1.4, ('10.0.0.4', '10.0.0.8'): 3.3 }
    # edge_info = {
    #     (1, 2): {('10.0.0.1', '10.0.0.5'): {0: 1, 1: 0, 2: 0}, ('10.0.0.2', '10.0.0.6'): {0: 1, 1: 0, 2: 0},
    #              ('10.0.0.3', '10.0.0.7'): {0: 1, 1: 0, 2: 0}, ('10.0.0.4', '10.0.0.8'): {0: 1, 1: 0, 2: 0}},
    #     (2, 3): {('10.0.0.1', '10.0.0.5'): {0: 1, 1: 0, 2: 0}, ('10.0.0.2', '10.0.0.6'): {0: 1, 1: 0, 2: 0},
    #              ('10.0.0.3', '10.0.0.7'): {0: 1, 1: 0, 2: 0}, ('10.0.0.4', '10.0.0.8'): {0: 1, 1: 0, 2: 0}},
    #     (3, 4): {('10.0.0.1', '10.0.0.5'): {0: 1, 1: 0, 2: 0}, ('10.0.0.2', '10.0.0.6'): {0: 1, 1: 0, 2: 0},
    #              ('10.0.0.3', '10.0.0.7'): {0: 1, 1: 0, 2: 0}, ('10.0.0.4', '10.0.0.8'): {0: 1, 1: 0, 2: 0}},
    #     (4, 6): {('10.0.0.1', '10.0.0.5'): {0: 1, 1: 0, 2: 0}, ('10.0.0.2', '10.0.0.6'): {0: 1, 1: 0, 2: 0},
    #              ('10.0.0.3', '10.0.0.7'): {0: 1, 1: 0, 2: 0}, ('10.0.0.4', '10.0.0.8'): {0: 1, 1: 0, 2: 0}},
    #     (1, 5): {('10.0.0.1', '10.0.0.5'): {0: 1, 1: 0, 2: 0}, ('10.0.0.2', '10.0.0.6'): {0: 1, 1: 0, 2: 0},
    #              ('10.0.0.3', '10.0.0.7'): {0: 1, 1: 0, 2: 0}, ('10.0.0.4', '10.0.0.8'): {0: 1, 1: 0, 2: 0}},
    #     (5, 6): {('10.0.0.1', '10.0.0.5'): {0: 1, 1: 0, 2: 0}, ('10.0.0.2', '10.0.0.6'): {0: 1, 1: 0, 2: 0},
    #              ('10.0.0.3', '10.0.0.7'): {0: 1, 1: 0, 2: 0}, ('10.0.0.4', '10.0.0.8'): {0: 1, 1: 0, 2: 0}},
    #     (6, 7): {('10.0.0.1', '10.0.0.5'): {0: 1, 1: 0, 2: 0}, ('10.0.0.2', '10.0.0.6'): {0: 1, 1: 0, 2: 0},
    #              ('10.0.0.3', '10.0.0.7'): {0: 1, 1: 0, 2: 0}, ('10.0.0.4', '10.0.0.8'): {0: 1, 1: 0, 2: 0}},
    #     (1, 8): {('10.0.0.1', '10.0.0.5'): {0: 1, 1: 0, 2: 0}, ('10.0.0.2', '10.0.0.6'): {0: 1, 1: 0, 2: 0},
    #              ('10.0.0.3', '10.0.0.7'): {0: 1, 1: 0, 2: 0}, ('10.0.0.4', '10.0.0.8'): {0: 1, 1: 0, 2: 0}},
    #     (8, 9): {('10.0.0.1', '10.0.0.5'): {0: 1, 1: 0, 2: 0}, ('10.0.0.2', '10.0.0.6'): {0: 1, 1: 0, 2: 0},
    #              ('10.0.0.3', '10.0.0.7'): {0: 1, 1: 0, 2: 0}, ('10.0.0.4', '10.0.0.8'): {0: 1, 1: 0, 2: 0}},
    #     (9, 10): {('10.0.0.1', '10.0.0.5'): {0: 1, 1: 0, 2: 0}, ('10.0.0.2', '10.0.0.6'): {0: 1, 1: 0, 2: 0},
    #              ('10.0.0.3', '10.0.0.7'): {0: 1, 1: 0, 2: 0}, ('10.0.0.4', '10.0.0.8'): {0: 1, 1: 0, 2: 0}},
    #     (2, 5): {('10.0.0.1', '10.0.0.5'): {0: 1, 1: 0, 2: 0}, ('10.0.0.2', '10.0.0.6'): {0: 1, 1: 0, 2: 0},
    #              ('10.0.0.3', '10.0.0.7'): {0: 1, 1: 0, 2: 0}, ('10.0.0.4', '10.0.0.8'): {0: 1, 1: 0, 2: 0}},
    #
    # }

    netmodel = NetModel(res_bw, flows, edge_info, path_num, flow_require)

    print(netmodel.main())