# --*-- coding:utf8 --*--
'''
@summary: Implementation of the NSGA-II algorithm in Python.
@version: 1.1
@since: 2018-01-10
@author: Marcelo Pita, http://marcelopita.wordpress.com & Yuan qijie
@contact: marcelo.souza.pita <at> gmail.com
@copyright: Copyright 2018 Marcelo Pita & Yuan Qijie
'''

import random
from nsga2Lib import Solution
from nsga2Lib import NSGAII
from NetworkModel import NetModel


class T1Solution(Solution):
    '''
    Solution for the T1 function.
    '''

    def __init__(self):
        '''
        Constructor.
        '''
        Solution.__init__(self, 2)
        # 生成的初始解,为每条数据流随机选择一条路径
        self.attributes = self.generate_new_solution()
        self.evaluate_solution()

    @staticmethod
    def generate_new_solution():
        '''
        生成一个解空间，确保该解有效，即分配的流量不超过承载的带宽。
        TODO：如何有效生成一个解
        '''
        while True:
            temp_solution = []
            for _ in range(flows_num):
                temp_solution.append(random.randint(0, path_num))
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
        child_solution = T1Solution()
        # for i in range(30):
        #     child_solution.attributes[i] = math.sqrt(self.attributes[i] * other.attributes[i])
        point = random.randint(0, flows_num - 1)
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
            attr[random.randint(0, flows_num-1)] = random.randint(0, path_num)
            if netmodel.solution_is_validate(attr):
                self.attributes = attr
                return
            round -= 1
        print('mutate failure')


def main():

    nsga2 = NSGAII(2, 0.1, 1.0)
    P = []
    # 初始化种群数量
    for i in range(70):
        P.append(T1Solution())

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
            chosen_path_dict[(flows[i])] = path_index - 1
    return chosen_path_dict, max_used_bandwidth


if __name__ == '__main__':
    res_bw = {(1, 2): 3, (1, 3): 3, (1, 4): 3, (2, 5): 3, (3, 7): 3, (4, 6): 3,
              (5, 7): 3, (6, 7): 3}
    flows = [('10.0.0.1', '10.0.0.4'), ('10.0.0.2', '10.0.0.5'), ('10.0.0.3', '10.0.0.6')]
    path_num = 3
    flows_num = len(flows)
    flow_require = {('10.0.0.1', '10.0.0.4'): 3, ('10.0.0.2', '10.0.0.5'): 2, ('10.0.0.3', '10.0.0.6'): 2}
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

    netmodel = NetModel(res_bw, flows, edge_info, path_num, flow_require)

    print(main())