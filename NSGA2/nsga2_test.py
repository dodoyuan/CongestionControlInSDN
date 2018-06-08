'''
@summary: Implementation of the NSGA-II algorithm in Python.
@version: 1.1
@since: 2018-01-10
@author: Marcelo Pita, http://marcelopita.wordpress.com & Yuan qijie
@contact: marcelo.souza.pita <at> gmail.com
@copyright: Copyright 2018 Marcelo Pita & Yuan Qijie
'''

import random, math
from nsga2Lib import Solution
from nsga2Lib import NSGAII


class T1Solution(Solution):
    '''
    Solution for the T1 function.
    '''

    def __init__(self):
        '''
        Constructor.
        '''
        Solution.__init__(self, 2)

        self.xmin = 0.0
        self.xmax = 1.0

        for _ in range(30):
            self.attributes.append(random.random())

        self.evaluate_solution()

    def evaluate_solution(self):
        '''
        Implementation of method evaluate_solution() for T1 function.
        '''
        self.objectives[0] = self.attributes[0]

        sum = 0.0
        for i in range(30):
            sum += self.attributes[i]

        g = 1.0 + (9.0 * (sum / 29))

        self.objectives[1] = g * (1.0 - math.sqrt(self.attributes[0] / g))

    def crossover(self, other):
        '''
        Crossover of T1 solutions.
        '''
        child_solution = T1Solution()

        for i in range(30):
            child_solution.attributes[i] = math.sqrt(self.attributes[i] * other.attributes[i])
        return child_solution

    def mutate(self):
        '''
        Mutation of T1 solution.
        '''
        self.attributes[random.randint(0, 29)] = random.random()


if __name__ == '__main__':
    nsga2 = NSGAII(2, 0.1, 1.0)

    P = []
    for i in range(50):
        P.append(T1Solution())

    nsga2.run(P, 50, 20)

    csv_file = open('nsga2_out.csv', 'a+')
    csv_file.write('----------------------------------------------\n')

    for i in range(len(P)):
        print P[i].attributes
        csv_file.write("" + str(P[i].objectives[0]) + ", " + str(P[i].objectives[1]) + "\n")

    csv_file.close()