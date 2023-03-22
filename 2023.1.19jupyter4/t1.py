import numpy as np
import matplotlib.pyplot as plt
import time
import datetime
import os
# #x = np.arange(10)
# x = [5, 6, 7, 8, 9, 10, 12, 13, 14, 16]
# # y = [1, 2, 2, 3, 5, 6, 8, 9, 10, 12]
# # y = [1, 1, 1, 1.5, 2, 3, 8, 9, 10, 12]
# # y = [1, 2, 5, 4, 5, 6, 8, 9, 10, 12]
# y = [1, 2, 5, 8, 11, 9, 7, 6, 3, 1]
# coeffs = np.polyfit(x, list(y), 1)
# print(coeffs)
# slope = coeffs[-2]
# print(slope)
# plt.plot(x, y)
# plt.show()

# t = 63775189237760.0   #broadband_timestamp
# t = 1641259801
# t = 1654084800.041
t = 1672965981.078
# k = time.ctime(t)
k = time.strftime('%Y%m%d %H:%M:%S', time.localtime(t))
print(k)
# t = 1653868798447
# t = 1654214398.037
# # k = time.ctime(t)
# k = time.strftime('%Y%m%d %H:%M:%S', time.localtime(t))
#
# print(k)
exit()

# # epoch = datetime.datetime(2021, 7, 7, 1, 2, 1).strftime('%s')
# # print(epoch)
# a4 = time.strftime("%S")
# print(a4)
# epoch_time = datetime.datetime(2021,11,24,8,0).timestamp()
# print(epoch_time)

# from pynput.keyboard import Key, Listener
# def show(key):
#     if key == Key.tab:
#         print("good")
#
#     if key != Key.tab:
#         print("try again")
#
#     # by pressing 'delete' button
#     # you can terminate the loop
#     if key == Key.escii:
#         return False
#
# # Collect all event until released
# with Listener(on_press=show) as listener:
#     listener.join()

# ta1 = time.strftime("%Y%m%d")
# ta2 = time.strftime("%H")
# ta3 = time.strftime("%M")
# print(ta1, ta2, ta3)
# epoch1 = datetime.datetime(int(ta1[:4]), int(ta1[4:6]), int(ta1[-2:]),int(ta2),int(ta3)).timestamp()
# epoch2 = epoch1+ 1200   ##20 min
# # k = time.ctime(epoch2)
# # print(k)
# k = time.strftime('%Y%m%d %H:%M:%S', time.localtime(epoch2))
# print(k)
# a2 = k[9:11]
# a3 = k[12:14]
# print('start at %s:%s! Wait until %s:%s to add sample'%(ta2, ta3, a2, a3))

# l1=[2, 4, 6, 7, 7, 8]
# zero1= np.mean(l1)
# print(zero1)
# print("hello %.2f"%(zero1))

xtruc = [2, 3, 4, 5, 6, 7]
ytruc = [2, 3, 6, 8, 11, 12]
x_t =    ['a', 'b', 'c', 'd', 'e', 'f']
# xloc = [0, 2, 5]
xloc = [2, 4, 7]
xmak = ['aa', 'b', 'egg']
fig, ax = plt.subplots()
# ax.plot(x_t, ytruc)
ax.plot(xtruc, ytruc)
ax.set_xticks(xloc, xmak)
plt.show()



