# !/usr/bin/env python
# --*--coding:utf8--*--

count = 0
with open('./h5.txt', 'r') as data, open('./h5_data.txt', 'a') as f:
    f.write('throughput \n')
    for line in data.readlines():
        # print line
        if len(line) > 34 and line[34] in "456":
            count += 1
            s = line[34:38] + ' ,'
            if count % 10 == 0:
                f.write('\n')
            f.write(s)

        # if len(line) > 34:
        #     if line[34] in '134':
        #         count += 1
        #         s = '%s, ' % (line[34:38])
        #         if count % 10 == 0:
        #             f.write('\n')
        #         f.write(s)
        #     if line[34] == ' ' and line[35] == '3':
        #         count += 1
        #         s = float(int(line[35:38])) / 1000
        #         s = '%s, ' % s
        #         if count % 10 == 0:
        #             f.write('\n')
        #         f.write(s)


# print 'count:', count