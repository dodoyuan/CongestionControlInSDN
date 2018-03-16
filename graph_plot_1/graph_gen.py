#! /usr/bin/env python
# --*-- coding:utf8--*--

from collections import defaultdict
#from shortestSum import mod_dijkstra
import numpy as np
import matplotlib.pyplot as plt
import all_data
from scipy import interpolate


def sender_plot():

    x = np.arange(0, 31, 1)

    y1 = all_data.sender_throughput.y1
    y2 = all_data.sender_throughput.y2
    y3 = all_data.sender_throughput.y3
    y4 = all_data.sender_throughput.y4

    # x = np.array(x)
    # y1 = np.array(y1)
    # xnew = np.linspace(x.min(), x.max(), 300)
    # y1_smooth = spline(x, y1, xnew)
    plt.figure(figsize=(8, 5))

    plt.plot(x, y1, 'k', marker='s', label="flow1 (h1-h5) ", markeredgewidth=1, mec='k',
             markerfacecolor="none", markersize=10)

    plt.plot(x, y2, 'r', marker='s', label="flow2 (h2-h6) ",
             markersize=10)

    plt.plot(x, y3, color='g', marker='h', markersize=10,
             label="flow3 (h3-h7)")

    plt.plot(x, y4, color='b', marker='o', markersize=10,
             label="flow4 (h4-h8)")

    plt.ylabel('Throughput(Mbps)')
    plt.xlabel('Time(s)')
    plt.yticks(np.arange(0, 4, 1))
    plt.legend(loc='upper left')
    plt.show()

def throughtout_plot():

    throughput_sp = [2.1, 2.7, 4.1, 5.8]
    throughput_ILP = [2.1, 2.7, 4.1, 7.4]
    throughput_greedy = [2.1, 2.7, 4.1, 7.4]

    n_groups = 4
    # create plot
    fig, ax = plt.subplots()
    index = np.arange(n_groups)
    bar_width = 0.15
    opacity = 0.5  # 透明度，0.5时候稍微好点
    rects1 = plt.bar(index + 0.1, throughput_sp, bar_width,
                     alpha=opacity,
                     color='grey', hatch='//',
                     label='shortest path')

    rects2 = plt.bar(index + 0.1 + bar_width, throughput_greedy, bar_width,
                     alpha=opacity,
                     color='lightgrey', hatch='\\',
                     label='greedy method')
    rects2 = plt.bar(index + 0.1 + 2 * bar_width, throughput_ILP, bar_width,
                     alpha=opacity,
                     color='lightgrey', hatch='--',
                     label='MILP method')

    plt.xlabel('time quantum')
    plt.ylabel('throughput(Mbps)')
    # plt.title('Scores by person')
    plt.yticks([0, 2, 4, 6, 8, 10])
    plt.xticks(index + 2 * bar_width, ('5s-10s', '10s-15s', '15s-20s', '20s-25s'))
    plt.legend(loc='upper left')  # 没有这个不会显示每个图的label

    # plt.tight_layout()  #去掉的话效果会更好点
    plt.show()

def ILP_plot():

    x = np.arange(0, 31, 1)

    y1 = all_data.ILP_throughput.y1
    y2 = all_data.ILP_throughput.y2
    y3 = all_data.ILP_throughput.y3
    y4 = all_data.ILP_throughput.y4

    plt.figure(figsize=(8, 5))
    plt.plot(x, y1, 'k', marker='s', label="flow(h1-h5) priority 4", markeredgewidth=1, mec='k',
             markerfacecolor="none", markersize=10)

    plt.plot(x, y2, 'r', marker='s', label="flow(h2-h6) priority 3",
             markersize=10)

    plt.plot(x, y3, color='g', marker='h', markersize=10,
             label="flow(h3-h7) priority 2")

    plt.plot(x, y4, color='b', marker='o', markersize=10,
             label="flow(h4-h8) priority 1")

    plt.ylabel('Throughput(Mbps)')
    plt.xlabel('Time(s)')
    plt.yticks(np.arange(0, 11, 1))
    plt.legend(loc='upper left')
    plt.show()

if __name__ == '__main__':
    sender_plot()
    throughtout_plot()
    # ILP_plot()

