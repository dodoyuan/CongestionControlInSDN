# /usr/bin/env python
# --*--coding:utf8--*--

import numpy as np
from matplotlib import pyplot as plt

# data to plot
# the data of graph1
# ---------------------4*4 mesh 5*5 mesh 6*6 mesh 20 random  30 random
ILP_packet_loss = [2, 0.28, 15, 59]
CSWP_packet_loss = [17, 0.18, 19, 0.15]

n_groups = 4

# create plot
fig, ax = plt.subplots()
index = np.arange(n_groups)
bar_width = 0.15
opacity = 0.5  # 透明度，0.5时候稍微好点

rects1 = plt.bar(index+0.1, ILP_packet_loss, bar_width,
                 alpha=opacity,
                 color='grey',hatch = '//',
                 label='packet loss rate with RR')

rects2 = plt.bar(index+0.1+ bar_width, CSWP_packet_loss, bar_width,
                 alpha=opacity,
                 color='lightgrey',hatch = '\\',
                 label='packet loss rate without RR')

plt.xlabel('flow topology')
plt.ylabel('path length')
#plt.title('Scores by person')
plt.yticks([0,10,20,30,40,50,60])
plt.xticks(index + 2*bar_width, ('flow1(h1-h5)', 'flow2(h2-h6)', 'flow3(h3-h7)', 'flow4(h4-h8)'))
plt.legend(loc='upper left')  # 没有这个不会显示每个图的label

# plt.tight_layout()  #去掉的话效果会更好点
plt.show()

