import time
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.animation import FuncAnimation
import numpy as np

from Listener_py3 import Listener
from queue import Queue
import StringPickler_py3 as StringPickler

# host = '10.100.4.20'  ## IP address
# port = 40060
# dm_queue = Queue(180)  #data manager=-
# listener = Listener(dm_queue, host, port, StringPickler.ArbitraryObject, retry=True)

# while True:
#     dm = dm_queue.get(timeout=5)
#     print(dm)
#     print(len(dm['data']))
# exit()

# i=0
# while True:
#     dm = dm_queue.get(timeout=5)
#     i += 1
#     if dm['source'] == 'analyze_VOC_broadband_cal':
#         print(dm)
#         print(len(dm['data']))
#         break
#     if i == 6:
#         print ('analyze_VOC_broadband_cal not exist. Your litho_fitter may stop running, '
#                'please start fitter and try again.')
# exit()

def specviewer(host, port, gas):
    dm_queue = Queue(180)  # data manager=-
    listener = Listener(dm_queue, host, port, StringPickler.ArbitraryObject, retry=True)
    n = 1000  ## x-axis number  1000: <1.5h
    x = []  ## unix time 1641259801
    xt = []  ## real time 19:30\nJan-3-2022
    y = []
    xx = []  ## x labels that will be marked
    # gas = 'MFC2_flow'
    # gas = 'broadband_gasConcs_280'

    ## add first element
    while True:
        dm = dm_queue.get(timeout=5)
        if dm['source'] == 'analyze_VOC_broadband_cal':
            t = dm['time']
            x.append(t)
            xt.append(time.ctime(t))
            y.append(dm['data'][gas])
        if len(y):
            break

    fig, ax = plt.subplots()

    def animate(i):
        dm = dm_queue.get(timeout=5)
        if dm['source']=='analyze_VOC_broadband_cal':
            print(i)
            if len(y) == n:
                x.pop(0)
                xt.pop(0)
                y.pop(0)

            t = dm['time']
            x.append(t)
            xt.append(time.ctime(t))
            y.append(dm['data'][gas])

            a = time.ctime(x[-2])
            b = time.ctime(t)

            if ((a.split(":")[1] == '59' and b.split(":")[1] == '00') or
                    (a.split(":")[1] == '29' and b.split(":")[1] == '30')):
                xx.append(t)

            if (len(xx) > 0) and (xx[0] < x[0]):
                xx.pop(0)

            x1 = []    ## tick locations
            x2 = []    ## tick marker final format
            for j in xx:
                x1.append(x.index(j))
                xtime = time.ctime(j).split()
                x2.append(xtime[3][:-3]+'\n'+xtime[1]+'-'+xtime[2]+'-'+xtime[4])
            # print(xx)
            # print(x1)
            # print(x2)

            ax.clear()
            ax.plot(xt, y)
            ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2e'))

            ## don't use plt, will set for all plots
            # ax.set_ylabel(gas)
            ax.set_xlabel('Time')
            ax.set_title(gas)

            if x1 == []:
                ax.set_xticklabels([])
            else:
                ax.set_xticks(x1, x2)

    # fig, ax = plt.subplots()
    ani = FuncAnimation(fig, animate, interval=1000)
    fig.canvas.manager.set_window_title('Spectrum Viewer Real Time')

    plt.show()

if __name__ == "__main__":
    host = '10.100.4.20'  ## IP address
    port = 40060
    gas = 'broadband_gasConcs_280'
    # gas = 'MFC2_flow'

    specviewer(host, port, gas)



#
# while True:
# # if 1:
#     dm = dm_queue.get(timeout=5)
#     if dm['source']=='analyze_VOC_broadband_cal':
#         xtime = time.ctime(dm['time'])
#         print(xtime)
#         # print(xtime.split())
#
#         # print(dm['data']['MFC1_flow'])
#         print(dm['data'][gas])
#         # print(dm['data']['broadband_gasConcs_962'])
#         # print(dm['data']['broadband_gasConcs_176'])
#         # print(dm[''])
#
#     # time.sleep(1)














