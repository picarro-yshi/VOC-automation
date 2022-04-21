import random
import time

import matplotlib.pyplot as plt
import pandas as pd
# for i in range(20):
#     # print(1-random.randint(1, 19)/100)
#     print(random.randint(1, 4)*5)

# # print(a)
# fn = 'sam1'
# df = pd.read_csv(fn + '.csv')
# # df1 = df.iloc[:, 1:]  # remove first column
# tc = df.iloc[:, 0]  # first column is time, s
# nr = df.shape[0]  # row number
# nc = df.shape[1]  # column number
#
# t1 = list(tc)
# t2 = []
# t3 = []
# sum = 0
# for t in t1:
#     t2.append(sum)
#     sum += t
#     t3.append(sum-1)
#
# print(t2)
# print(sum)

# a = 2
# b = 5
# print(b%a)

# print(int(time.time()))
# print(time.strftime("%H:%M"))

a = [1, 2, 3, 4, 5]
b = [2, 3, 4, 6, 8]
# plt.plot(a, b)
fig, ax = plt.subplots()
# ax.plot_date(a, b)
ax.plot(a, b)
x1=[3, 4]
x2 = ['aob', 'boc']
ax.set_xticks(x1, x2)
#
# a.pop(0)
# b.pop(0)
#
# ax.plot(a, b)
# x1=[4, 3]
# x2 = ['a', 'b']
# ax.set_xticks(x1, x2)
#
plt.show()

# a = []
# print(len(a))

exit()

# a = 2
# b = 1
# c = 3
# d = 0
# if ((a>1) or (b>2) or (c>4) or (d>0)):
#     print('ok')


# a = []
# b=np.mean(a)
# c = 4
# print(b)
# if c>b*1.2:
#     print('ok')

# a= [1, 2, 3, 5, 6, 7]
# b = a[:-3]
# print(b)
# exit()


df1 = pd.read_csv('sam1.csv')
# print(df.head())

# X, Y = df['bottle concentration'].to_numpy(), df['c measure'].to_numpy()
# ones = np.ones(X.shape)
# f1=df['f1']
tc = df1.iloc[:, 0]  # first column is time, s
# for t in tc:
#     print (t)

df = df1.iloc[:, 1:]  #remove first column
# print(t[0])
# exit()

# df.drop(columns=df.columns[0], axis=1, inplace=True)

# f1=df.iloc[0]   # each row
# for i in f1:
#     print(i)

nr = df.shape[0]   #row number
nc = df.shape[1]   #column number
# print(nr)
# print(nc)
# for i in range(nc):
#     print(f1[i])
# exit()
