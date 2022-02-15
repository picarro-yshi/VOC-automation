#!/usr/bin/python3
#
# File Name: Listener.py
# Purpose: Listener is used to subscribe to a broadcast, optionally calling a "filter"
#  function on the data, and then optionally placing it in a queue. The objects sent by the
#  broadcast are assumed to be string pickled instances of some ctypes class.
#
# Notes: For text broadcasts, use TextListener.py
#
# File History:
# 05-??-?? sze   Created file
# 05-12-04 sze   Added this header
# 06-01-04 sze   Trap empty string from socket recv
# 06-10-30 russ  Arbitrary object serialization support
# 07-10-22 sze   Add a name and logFunc parameters to constructor so that we can log connections by name
# 07-11-24 sze   If an error occurs in the processing (filtering) of a packet, break the connection and retry
#                   (if this is requested)
# 14-06-29 sze   Use 0MQ PUB-SUB protocol instead of TCP Sockets
# 17-02-16 sze   Added autoDropOldest parameter
import ctypes
import threading
import time
import traceback
from queue import Empty, Full, Queue
from typing import Any, Callable, Dict, List, Optional, Union
import zmq
import StringPickler_py3 as StringPickler

# ipadd = '10.100.4.20'

class Listener(threading.Thread):
    """ Listener object which allows access to broadcasts via ZMQ sockets """
    def __init__(self,
                 queue: Optional[Queue],
                 host: str,
                 port: int,
                 elementType: Any,
                 streamFilter: Optional[Callable] = None,
                 # host: str = "localhost",
                 notify: Optional[Callable] = None,
                 retry: bool = False,
                 name: str = "Listener",
                 logFunc: Optional[Callable] = None,
                 autoDropOldest: bool = False) -> None:
        """ Create a listener running in a new daemonic thread which subscribes to broadcasts at
        the specified "port". The broadcast consists of entries of type "elementType" (a subclass of
        ctypes.Structure)

        As elements arrive, they may be processed by the streamFilter function, and the results
        placed on a queue (an instance of Queue.Queue). Either of these parameters may be set to None.
        If the streamFilter is None, the entire entry is forwarded for queueing. If the queue is None,
        the data are discarded after calling streamFilter.

        The streamFilter function executes in the context of the Listener thread. It may be used to
        execute arbitrary code although it is primarily intended to be a filter which extracts the desired
        data from the elements and queues it for the main thread. By returning None nothing is queued, thus
        allowing data to be discarded.

        Information placed on the queue may be processed by a thread (usually the main thread) which gets
        from the queue. If all the processing can be done in the listener thread, the queue may be set to
        None.

        The parameters "notify" and "retry" control how errors which occur within the thread (including within
        the streamFilter) are handled. "notify" is a function or None, while "retry" is a boolean.

        notify is None,      retry == False: An exception kills the thread, and is raised
        notify is not None , retry == False: An exception invokes notify(exception_object) and kills the thread
        notify is None,      retry == True:  An exception is ignored, and processing continues
        notify is not None,  retry == True:  An exception invokes notify(exception_object) and processing continues

        A common exception occurs if the listener cannot contact the broadcaster. By setting retry=True, the
        listener will wait until the broadcaster restarts.

        The parameters "name" and "logFunc" are useful for debugging. Mesages from this module are sent by calling
        "logFunc", passing a string which includes "name". If "logFunc" is set to None, no logging takes place.

        The "autoDropOldest" parameter, if True, will cause the oldest data to be automatically removed from
        the queue if the queue is full when new data arrive, rather than raise an exception.
        """
        threading.Thread.__init__(self, name=name)
        self._stopevent = threading.Event()
        self.data = b""  # type: bytes
        self.queue = queue  # type: Optional[Queue]
        self.host = host  # type: str
        self.port = port  # type: int
        self.streamFilter = streamFilter  # type: Optional[Callable]
        self.elementType = elementType  # type: Any
        self.IsArbitraryObject = False  # type: bool
        self.name = name  # type: str
        self.logFunc = logFunc  # type: Optional[Callable]
        self.notify = notify  # type: Optional[Callable]
        self.retry = retry  # type: bool
        self.autoDropOldest = autoDropOldest  # type: bool

        try:
            if StringPickler.ArbitraryObject in self.elementType.__mro__:
                self.IsArbitraryObject = True
        except:
            pass
        if not self.IsArbitraryObject:
            self.recordLength = ctypes.sizeof(self.elementType)

        self.zmqContext = zmq.Context()  # type: zmq.Context
        self.socket = None  # type: Optional[zmq.socket]
        self.setDaemon(True)
        self.start()

    def safeLog(self, msg: str, *args: Any, **kwargs: Any) -> None:
        try:
            if self.logFunc is not None:
                self.logFunc(msg, *args, **kwargs)
        except:
            pass

    def stop(self, timeout: Optional[float] = None) -> None:
        """ Used to stop the main loop.
        This blocks until the thread completes execution of its .run() implementation.
        """
        self._stopevent.set()
        if self.socket is not None:
            self.socket.close()
            self.socket = None
        self.zmqContext.term()
        self.zmqContext = None
        threading.Thread.join(self, timeout)

    def run(self) -> None:
        poller = None  # type: zmq.Poller
        while not self._stopevent.is_set():
            try:
                if self.socket is None:
                    try:
                        poller = zmq.Poller()
                        self.socket = self.zmqContext.socket(zmq.SUB)
                        if self.socket is None:
                            raise RuntimeError
                        self.socket.connect("tcp://%s:%s" % (self.host, self.port))
                        self.socket.setsockopt(zmq.SUBSCRIBE, b"")
                        poller.register(self.socket, zmq.POLLIN)
                        self.safeLog("Connection made by %s to port %d." % (self.name, self.port))
                    except Exception:
                        self.socket = None
                        if self.notify is not None:
                            msg = "Attempt to connect port %d by %s failed." % (self.port, self.name)
                            self.safeLog(msg)
                            self.notify(msg)
                        time.sleep(1.0)
                        if self.retry:
                            continue
                        else:
                            return
                    self.data = b""
                try:
                    socks = dict(poller.poll(timeout=1000))  # type: Dict[zmq.socket, Any]
                    if socks.get(self.socket) == zmq.POLLIN:
                        self.data += self.socket.recv()
                except Exception as e:  # Error accessing or reading from socket
                    self.safeLog("Error accessing or reading from port %d by %s. Error: %s." % (self.port, self.name, e))
                    if self.socket is not None:
                        self.socket.close()
                        self.socket = None
                    continue
                # All received bytes are now appended to self.data
                if self.IsArbitraryObject:
                    self._ProcessArbitraryObjectStream()
                else:
                    self._ProcessCtypesStream()
            except Exception as e:
                self.safeLog("Communication from %s to port %d disconnected." % (self.name, self.port),
                             verbose=traceback.format_exc())
                if self.socket is not None:
                    self.socket.close()
                    self.socket = None
                if self.retry:
                    if self.notify is not None:
                        self.notify(e)
                    continue
                else:
                    if self.notify is not None:
                        self.notify(e)
                        return
                    else:
                        raise

    def _ProcessArbitraryObjectStream(self) -> None:
        while 1:
            try:
                obj, residual = StringPickler.unpack_arbitrary_object(self.data)  # type: Any, bytes
                if self.streamFilter is not None:
                    obj = self.streamFilter(obj)
                if obj is not None and self.queue is not None:
                    while True:
                        try:
                            self.queue.put_nowait(obj)
                            break
                        except Full:
                            if self.autoDropOldest:
                                self.queue.get_nowait()
                            else:
                                raise
                self.data = residual
            except StringPickler.IncompletePacket:
                # All objects have been stripped out.  Get out of the loop to
                # get more data...
                break
            except StringPickler.ChecksumErr:
                raise
            except StringPickler.BadDataBlock:
                raise
            except StringPickler.InvalidHeader:
                raise

    def _ProcessCtypesStream(self) -> None:
        while len(self.data) >= self.recordLength:
            result = StringPickler.bytes_as_object(self.data[0:self.recordLength], self.elementType)  # type: Any
            if self.streamFilter is not None:
                obj = self.streamFilter(result)  # type: Any
            else:
                obj = result
            if obj is not None and self.queue is not None:
                while True:
                    try:
                        self.queue.put_nowait(obj)
                        break
                    except Full:
                        if self.autoDropOldest:
                            self.queue.get_nowait()
                        else:
                            raise
            self.data = self.data[self.recordLength:]

#### below code does not run because Host function sits on analyzer and old python2 version conflict
if __name__ == "__main__":
    import ctypes
    import Host.Common.StringPickler as StringPickler
    from Host.Common.StringPickler import ArbitraryObject

    class MyTime(ctypes.Structure):
        _fields_ = [
            ("tm_year", ctypes.c_int),
            ("tm_mon", ctypes.c_int),
            ("tm_mday", ctypes.c_int),
            ("tm_hour", ctypes.c_int),
            ("tm_min", ctypes.c_int),
            ("tm_sec", ctypes.c_int),
        ]

    def myNotify(e: str) -> None:
        print("Notification: %s" % (e, ))

    def myLogger(s: str) -> None:
        print("Log: %s" % (s, ))

    def myFilter(m: Any) -> Any:
        assert isinstance(m, MyTime * 10000)
        return m

    q = Queue(0)  # type: Queue
    port = 8881
    host = '10.100.4.20'

    use_arbitrary_object_pickler = False

    if use_arbitrary_object_pickler:
        listener = Listener(q, port, ArbitraryObject, retry=True, notify=myNotify, name="Test Listener", logFunc=myLogger)
    else:
        listener = Listener(q, port, MyTime * 10000, myFilter, retry=True, notify=myNotify, name="Test Listener", logFunc=myLogger)

    while listener.is_alive():
        try:
            result = q.get(timeout=0.5)
            h, m, s = result[0].tm_hour, result[0].tm_min, result[0].tm_sec
            print("Time is %02d:%02d:%02d" % (h, m, s))
        except Empty:
            continue

    print("Listener terminated")
