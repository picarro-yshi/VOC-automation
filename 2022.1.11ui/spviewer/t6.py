from Listener_py3 import Listener
from queue import Queue
import StringPickler_py3 as StringPickler

host = '10.100.4.20'  ## IP address
port = 40060
dm_queue = Queue(180)
listener = Listener(dm_queue, host, port, StringPickler.ArbitraryObject, retry=True)

def handler(signum, frame):
    print("Forever is over!")
    raise Exception("end of time")

def loop_forever():
    i = 1
    while True:
    # if 1:
        data = dm_queue.get()
        print(data)
        print (i)
        i+=1

# def loop_forever():
#     import time
#     while 1:
#         print("sec")
#         time.sleep(1)

import signal
signal.signal(signal.SIGALRM, handler)
signal.alarm(10)



try:
   loop_forever()
except Exception as exc:
   print(exc)











