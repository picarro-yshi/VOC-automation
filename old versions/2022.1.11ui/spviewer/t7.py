import time

from Listener_py3 import Listener
from queue import Queue
import StringPickler_py3 as StringPickler

host = '10.100.4.20'  ## IP address
port = 40060
dm_queue = Queue(180)  #data manager
listener = Listener(dm_queue, host, port, StringPickler.ArbitraryObject, retry=True)

xvar = 1640042347.919
xtime = time.ctime(xvar).split()
print(xtime[3]+' '+xtime[1]+'-'+xtime[2]+'-'+xtime[4])
exit()

while True:
# if 1:
    dm = dm_queue.get(timeout=5)
    if dm['source']=='analyze_VOC_broadband_cal':
        xtime = time.ctime(dm['time'])
        print(xtime)
        # print(xtime.split())

        # print(dm)
        # print(len(dm['data']))
        # print(dm['time'])
        # print(dm['data']['MFC1_flow'])
        print(dm['data']['MFC2_flow'])
        # print(dm['data']['broadband_gasConcs_962'])
        # print(dm['data']['broadband_gasConcs_176'])
        # print(dm[''])

    # time.sleep(1)














