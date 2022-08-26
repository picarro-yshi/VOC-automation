from Listener_py3 import Listener
# from queue import Queue
from queue import Empty, Full, Queue
import StringPickler_py3 as StringPickler

host = '10.100.4.20'  ## IP address
port = 40060
dm_queue = Queue(180)
listener = Listener(dm_queue, host, port, StringPickler.ArbitraryObject, retry=True)

def loop_forever():
    while listener.is_alive():
        try:
            result = dm_queue.get(timeout=5)
            print(result['good'])
        # except Empty:
        except:
            print('no data')
            continue
            # break


if __name__=='__main__':
    loop_forever()
    print("Listener terminated")










