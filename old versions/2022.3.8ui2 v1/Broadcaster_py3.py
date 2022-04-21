   #!/usr/bin/python3
#
# File Name: Broadcaster.py
# Purpose: Broadcaster is a class which allows multiple clients to connect to a TCP socket and
#  receive data which is broadcasted to all of them. A client may disconnect at any time without
#  affecting the other clients.
#
# Notes:
#
# File History:
# 05-??-?? sze   Created file
# 05-12-04 sze   Added this header
# 06-03-10 sze   Removed assert statements
# 07-09-06 sze   Introduced safeLog function
# 08-03-05 sze   Return queue length during put to message Queue
# 08-04-23 sze   Ensure that listen socket is closed when broadcaster thread stops
# 09-10-23 sze   Simplified to do queuing in kernel
# 14-06-29 sze   Use 0MQ PUB-SUB protocol instead of TCP Sockets

from typing import Any, Callable, Dict, List, Optional, Union

import zmq


class Broadcaster(object):

    def __init__(self, port: int, name: str='Broadcaster', logFunc: Optional[Callable]=None,
                 sendHwm: int=500) -> None:
        self.name = name
        self.port = port
        self.logFunc = logFunc
        self.zmqContext = zmq.Context()  # type: zmq.Context
        self.publisher = self.zmqContext.socket(zmq.PUB)  # type: zmq.socket
        # Prevent publisher overflow from slow subscribers
        self.publisher.setsockopt(zmq.SNDHWM, sendHwm)
        self.publisher.bind("tcp://*:%s" % port)

    def send(self, msg: bytes) -> None:
        self.publisher.send(msg)

    def stop(self) -> None:
        self.publisher.close()
        self.publisher = None
        self.zmqContext.term()
        self.zmqContext = None


if __name__ == "__main__":
    from time import localtime, sleep, asctime
    import ctypes
    import StringPickler

    class MyTime(ctypes.Structure):
        _fields_ = [
            ("tm_year", ctypes.c_int),
            ("tm_mon", ctypes.c_int),
            ("tm_mday", ctypes.c_int),
            ("tm_hour", ctypes.c_int),
            ("tm_min", ctypes.c_int),
            ("tm_sec", ctypes.c_int),
        ]

    def myLog(msg: str) -> None:
        print(msg)

    use_arbitrary_object_pickler = False
    b = Broadcaster(8881, logFunc=myLog, sendHwm=10)
    m = (MyTime * 10000)()
    l = []
    while True:
        t = localtime()
        for i in range(10000):
            m[i].tm_year = t.tm_year
            m[i].tm_month = t.tm_mon
            m[i].tm_mday = t.tm_mday
            m[i].tm_hour = t.tm_hour
            m[i].tm_min = t.tm_min
            m[i].tm_sec = t.tm_sec
            l.append(t)
        if use_arbitrary_object_pickler:
            b.send(StringPickler.pack_arbitrary_object(l))
        else:
            b.send(StringPickler.object_as_bytes(m))

        #b.send(bytes(asctime(), "ascii"))
        sleep(1.0)