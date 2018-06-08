# --*-- coding:utf8 --*--
'''
@summary: Implementation of the NSGA-II algorithm in Python.
@version: 1.2
@since: 2018-01-07
@author: Marcelo Pita, http://marcelopita.wordpress.com & Yuan Qijie
'''

import sys, random


class Solution:
    '''
    Abstract solution. To be implemented.
    '''

    def __init__(self, num_objectives):
        '''
        Constructor. Parameters: number of objectives.
        '''
        self.num_objectives = num_objectives
        self.objectives = []
        for _ in range(num_objectives):
            self.objectives.append(None)
        self.attributes = []
        # self.rank = sys.maxint
        self.distance = 0.0

    def evaluate_solution(self):
        '''
        Evaluate solution, update objectives values.
        '''
        raise NotImplementedError("Solution class have to be implemented.")

    def crossover(self, other):
        '''
        Crossover operator.
        '''
        raise NotImplementedError("Solution class have to be implemented.")

    def mutate(self):
        '''
        Mutation operator.
        '''
        raise NotImplementedError("Solution class have to be implemented.")

    def __rshift__(self, other):
        '''
        True if this solution dominates the other (">>" operator).
        对 '>>'进行重写 ，这里还是做了简化，采用的是严格大于。
        '''
        dominates = False

        for i in range(len(self.objectives)):
            if self.objectives[i] > other.objectives[i]:
                return False

            elif self.objectives[i] < other.objectives[i]:
                dominates = True

        return dominates

    def __lshift__(self, other):
        '''
        True if this solution is dominated by the other ("<<" operator).
        '''
        return other >> self


def crowded_comparison(s1, s2):
    '''
    Compare the two solutions based on crowded comparison.
    '''
    # if s1.rank < s2.rank:
    #     return 1
    #
    # elif s1.rank > s2.rank:
    #     return -1

    if s1.distance > s2.distance:
        return 1

    elif s1.distance < s2.distance:
        return -1

    else:
        return 0


class NSGAII:
    '''
    Implementation of NSGA-II algorithm.
    '''
    current_evaluated_objective = 0

    def __init__(self, num_objectives, mutation_rate=0.1, crossover_rate=1.0):
        '''
        Constructor. Parameters: number of objectives, mutation rate (default value 10%) and crossover rate (default value 100%).
        '''
        self.num_objectives = num_objectives
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate

        # random.seed()

    def run(self, P, population_size, num_generations):
        '''
        Run NSGA-II.
        '''
        # for s in P:
        #     s.evaluate_solution()

        Q = []
        # 循环代数，引入了精英策略
        for i in range(num_generations):
            print "Iteracao ", i

            R = []
            R.extend(P)
            R.extend(Q)

            fronts = self.fast_nondominated_sort(R)

            del P[:]  # P = []
            # 从front中选出population_size大小的个体作为本次结果
            left_number = population_size
            for front in fronts.values():
                # question: 有没有必要所有的都计算一遍拥挤度
                self.crowding_distance_assignment(front)
                if len(front) < left_number:
                    P.extend(front)
                    left_number -= len(front)
                else:
                    self.sort_crowding(front)
                    P.extend(front[:left_number])
                    break

            Q = self.make_new_pop(P)

    def sort_objective(self, P, obj_idx):
        # 比较基本的简单选择排序
        for i in range(len(P) - 1, -1, -1):
            for j in range(1, i + 1):
                s1 = P[j - 1]
                s2 = P[j]

                if s1.objectives[obj_idx] > s2.objectives[obj_idx]:
                    P[j - 1] = s2
                    P[j] = s1

    def sort_crowding(self, P):
        for i in range(len(P) - 1, -1, -1):
            for j in range(1, i + 1):
                s1 = P[j - 1]
                s2 = P[j]
                # 如果s1的拥挤度小于s2的拥挤度，则说明要交换位置。
                # 说明是按照拥挤度从大到小排序，也就是说拥挤度越大个体会被选择
                if s1.distance < s2.distance:
                    P[j - 1] = s2
                    P[j] = s1

    def make_new_pop(self, P):
        '''
        Make new population Q, offspring of P.
        '''
        Q = []

        while len(Q) != len(P):
            selected_solutions = [None, None]

            # 选出两个父本，用作产生子代
            while selected_solutions[0] == selected_solutions[1]:
                for i in range(2):
                    s1 = random.choice(P)
                    s2 = s1
                    while s1 == s2:
                        s2 = random.choice(P)

                    if crowded_comparison(s1, s2) > 0:
                        selected_solutions[i] = s1

                    else:
                        selected_solutions[i] = s2

            if random.random() < self.crossover_rate:
                child_solution = selected_solutions[0].crossover(selected_solutions[1])

                if random.random() < self.mutation_rate:
                    child_solution.mutate()

                child_solution.evaluate_solution()

                Q.append(child_solution)

        return Q

    def fast_nondominated_sort(self, P):
        '''
        Discover Pareto fronts in P, based on non-domination criterion.
        对种群P进行非支配排序，返回字典，{1:[p1,p2,p3...], 2:[...]}
        '''
        fronts = {}

        S = {}
        n = {}
        for s in P:
            S[s] = []
            n[s] = 0

        fronts[1] = []

        for p in P:
            for q in P:
                if p == q:
                    continue

                if p >> q:
                    S[p].append(q)

                elif p << q:
                    n[p] += 1

            if n[p] == 0:
                fronts[1].append(p)

        i = 1
        while len(fronts[i]) != 0:
            next_front = []
            for r in fronts[i]:
                for s in S[r]:
                    n[s] -= 1
                    if n[s] == 0:
                        next_front.append(s)

            i += 1
            fronts[i] = next_front
        return fronts

    def crowding_distance_assignment(self, front):
        '''
        Assign a crowding distance for each solution in the front.
        '''
        for p in front:
            p.distance = 0

        for obj_index in range(self.num_objectives):
            self.sort_objective(front, obj_index)

            front[0].distance = float('inf')
            front[len(front) - 1].distance = float('inf')

            for i in range(1, len(front) - 1):
                # original implement, seem some wrong
                # front[i].distance += (front[i + 1].distance - front[i - 1].distance)
                front[i].distance += (front[i + 1].objectives[obj_index] - front[i - 1].objectives[obj_index])
