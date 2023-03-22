#!/usr/bin/python
#
# FILE:
#   CmdFIFO.py
#
# DESCRIPTION:
#   Remote procedure call framework built on top of Pyro which allows functions
#    to be called across a local or networked TCP/IP connection. A CmdFIFO server
#    accepts connections from one or more clients, who request that functions be
#    executed on their behalf. These functions are typically enqueued in order of
#    receipt, and are executed sequentially. Remote procedure calls may be set
#    up to block until completion, return immediately, or initiate a callback
#    on completion. High priority functions may also be defined, which bypass the
#    enqueing process.
#
# SEE ALSO:
#   Specify any related information.
#
# HISTORY:
#   18-Aug-2008  sze  Initial version to work with Pyro, almost totally rewritten
#                      from Russ' XML/RPC based code which was having occasional
#                      socket timeout errors.
#   28-Jun-2014  sze  Ported to use Pyro4
#
#  Copyright (c) 2008-2014 Picarro, Inc. All rights reserved
#
import Pyro4
import logging
import os
import pydoc
from select import select
import threading
import traceback
import re
import sys
import time
import types

# This version requires Pyro4 v 4.43 because of a change in how internal class
# methods and members can be exposed.
# See commit beb30d316011367b70044f5d05bc4b43297928ad in picarro/Host
#
if float(Pyro4.__version__) < 4.43:
    raise RuntimeError("CmdFIFO requires Pyro4 v4.43")

# set some constants (using chars to make easier to decipher and avoid lookups)
CMD_TYPE_Default = "D"  # 0 #Block until complete, then return to client
CMD_TYPE_Blocking = "B"  # 1 #Block until complete, then return to client
CMD_TYPE_VerifyOnly = "V"  # 2 #Return immediately to client.  Return is lost.
CMD_TYPE_Callback = "C"  # 3 #Confirm receipt, then execute callback when done.
CMD_TYPE_ERROR = "E"  # -1

CMD_Types = [
    CMD_TYPE_Default,
    CMD_TYPE_Blocking,
    CMD_TYPE_VerifyOnly,
    CMD_TYPE_Callback,
    CMD_TYPE_ERROR
]

uriRegex = re.compile("http://(.*):(\d+)")
Pyro4.config.SERIALIZER = 'pickle'
Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle')
# print(Pyro4.config.PICKLE_PROTOCOL_VERSION)    ### 5
Pyro4.config.PICKLE_PROTOCOL_VERSION = 2

class RemoteException(RuntimeError):
    pass

# @decorator
# def rpc_wrap(func, *a, **k):
#    try:
#        return func(*a, **k)
#    except:
#        raise RemoteException(traceback.format_exc())


def rpc_wrap(func):
    def wrapper(*a, **k):
        try:
            return func(*a, **k)
        except:
            raise RemoteException(traceback.format_exc())
    wrapper.__wrapped_co_argcount = func.__code__.co_argcount
    wrapper.__wrapped_co_varnames = func.__code__.co_varnames
    wrapper.__wrapped_defaults = func.__defaults__
    wrapper.__wrapped_doc = pydoc.getdoc(func)
    return wrapper


def resolve_dotted_attribute(obj, attr, allow_dotted_names=True):
    """resolve_dotted_attribute(a, 'b.c.d') => a.b.c.d

    Resolves a dotted attribute name to an object.  Raises
    an AttributeError if any attribute in the chain starts with a '_'.

    If the optional allow_dotted_names argument is false, dots are not
    supported and this function operates similar to getattr(obj, attr).
    """

    if allow_dotted_names:
        attrs = attr.split('.')
    else:
        attrs = [attr]

    for i in attrs:
        if i.startswith('_'):
            raise AttributeError(
                'attempt to access private attribute "%s"' % i
            )
        else:
            obj = getattr(obj, i)
    return obj


def list_public_methods(obj):
    """Returns a list of attribute strings, found in the specified
    object, which represent callable attributes"""

    return [member for member in dir(obj)
            if not member.startswith('_') and
            callable(getattr(obj, member))]


def remove_duplicates(lst):
    """remove_duplicates([2,2,2,1,3,3]) => [3,1,2]

    Returns a copy of a list without duplicates. Every list
    item must be hashable and the order of the items in the
    resulting list is not defined.
    """
    u = {}
    for x in lst:
        u[x] = 1

    return list(u.keys())


class DaemonicThread(threading.Thread):
    def __init__(self, *a, **k):
        threading.Thread.__init__(self, *a, **k)
        self.setDaemon(True)


class CmdFIFOError(Exception):
    pass


class TimeoutError(CmdFIFOError):
    pass


class ShutdownInProgress(CmdFIFOError):
    pass


class KillInProgress(ShutdownInProgress):
    pass


class DummyDaemon(object):
    """Stub for compatibility with Pyro3"""

    def __init__(self, pyroDaemon):
        self.pyroDaemon = pyroDaemon
        self.mustShutdown = False

    def handleRequests(self, timeout=0.5, others=None, callback_func=None):
        rs = set(self.pyroDaemon.sockets)
        if others is None:
            others = []
        others = set(others)
        rs.update(others)
        rr, _, _ = select(rs, [], [], timeout)
        rPyro = rs.intersection(rr)
        if rPyro:
            self.pyroDaemon.events(rPyro)
        rOthers = others.intersection(rr)
        if rOthers and (callback_func is not None):
            callback_func(list(rOthers))


class CmdFIFOServer(object):
    loggerInst = 0

    @Pyro4.expose
    class CallbackObject(object):
        """This class is used to instntiate an object which is accessible via the Pyro protocol. It contains a dispatch method which allows callback functions previously registered using register_callback_fuction to be executed"""

        def __init__(self, server):
            self.server = server
            # Dictionary of callback functions indexed by name
            self.funcs = {}

        def __dispatch__(self, dottedMethodName, a, k):
            """Dispatches the dottedMethodName applied to the arguments *a, **k."""
            method = dottedMethodName
            try:
                func = self.funcs[method]
            except KeyError:
                raise CmdFIFOError(
                    'Callback method "%s" is not supported' % method)
            return func(*a, **k)

    @Pyro4.expose
    class ServerObject(object):
        def __init__(self, server):
            self.instance = None
            self.server = server
            self.allowDottedNames = False
            self.funcs = {}
            self.funcModes = {}
            self.priorityFunctions = []
            self.eventLock = threading.Lock()
            self.event = threading.Event()
            self.queueLength = 0
            self.event.set()

        def __dispatch__(self, dottedMethodName, client, modeOverride, callbackInfo, a, k):
            """Dispatches the dottedMethodName applied to the arguments *a, **k.
            The method may be a registered function, or a method of the registered
            instance. Depending on whether the method is registered as a priority
            function or as a normal function, it is either executed immediately or
            is enqueued for execution in sequence. Non-priority functions can be
            executed in several modes:
                CMD_TYPE_Blocking   Calling thread blocks, function is enqueued and
                  executed in sequence. Calling thread resumes and receives return
                  value of the function on completion.
                CMD_TYPE_VerifyOnly Calling thread submits a function to be enqueued.
                  Caller does not block, but receives an "OK" response. The enqueued
                  function is executed in sequence within a daemonic thread.
                CMD_TYPE_Callback   Calling thread submits a function to be enqueued.
                  Caller does not block, but receives a  "CB" response. The enqueued
                  function is executed in sequence within a daemonic thread. After
                  the function is completed, the result and any exception are sent
                  as arguments to a remote callback function. This callback function must
                  have been registered as such by the client who must also provide a
                  callback server for this purpose. The callback server address and
                  function are specified by the client using the SetFunctionMode method
                  of its CmdFIFOServerProxy.
            The mode for each function is specified when it is registered with the server,
             but this can be overridden using the modeOverride parameter which is set up by
             the client via the CmdFIFOServerProxy.

            Stopping execution of the CmdFIFO server is done by issuing a CmdFIFO.StopServer
              or a CmdFIFO.KillServer command. The former closes down the server once there
              are no further requests to service while the latter closes down the server when
              the current request is complete. Once either of these requests is made,
              no further requests may be enqueued.
            """
            if self.server.ServerStopRequested or self.server.ServerKillRequested:
                raise ShutdownInProgress(
                    "RPC ignored because server is shutting down")

            method = dottedMethodName
            # Special case of CmdFIFO.StopServer: We need to set the ServerStopRequested flag
            #  immediately, so that subsequent RPC calls are refused, but the stop_server command
            #  is still enqueued so that the server shuts down once the queue is empty.
            if method == "CmdFIFO.StopServer":
                self.server.ServerStopRequested = True

            func = None
            try:
                # check to see if a matching function has been registered
                func = self.funcs[method]
                funcMode = self.funcModes[method]
            except KeyError:
                # Use an method of the registered instance
                funcMode = CMD_TYPE_Blocking
                if self.instance is not None:
                    # check for a __dispatch__ method
                    if hasattr(self.instance, '__dispatch__'):
                        func = lambda *a, **k: self.instance.__dispatch__(
                            method, a, k)
                    else:
                        # call instance method directly
                        try:
                            func = resolve_dotted_attribute(
                                self.instance,
                                method,
                                self.allow_dotted_names
                            )
                        except AttributeError:
                            pass

            if func is None:
                raise CmdFIFOError('Method "%s" is not supported' % method)

            if self.server.logRequests and self.server.logger != None:
                # Write the arguments in standard form, positional arguments followed by keyword arguments
                argStr = ",".join(["%r" % (arg,) for arg in a] +
                                  ["%s=%r" % (key, k[key]) for key in k])
                self.server.logger.info("%s calls %s(%s)" %
                                        (client, method, argStr))

            if method in self.priorityFunctions:
                # Skip serialization for priority functions
                return func(*a, **k)

            # To serialize execution of non-priority functions, a collection of Events
            #  is used. The attribute self.event names the event which the next
            #  function needs to wait upon. Access to self.event is protected by
            #  self.eventLock.
            #
            #  Each blocking function waits on an event to become set.
            #  Each non-blocking function spawns a thread which waits for an event to
            #   become set.
            # After each function completes, it sets the next Event object to start
            #  execution of the next function.
            # Setting events are in "finally" clauses. Otherwise, if an error occurs
            #  within a function, the queue stalls.

            # Get the time at which the function is enqueued
            rxTime = time.time()
            self.eventLock.acquire()
            try:
                self.queueLength += 1
                myEvent = self.event
                nextEvent = threading.Event()
                self.event = nextEvent
                # Do not allow next function to run yet
                nextEvent.clear()
            finally:
                # print "Putting method %s(%s,%s) on queue, length %d" % (method,a,k,self.queueLength)
                self.eventLock.release()

            if modeOverride != CMD_TYPE_Default:
                funcMode = modeOverride

            if funcMode == CMD_TYPE_Blocking:
                myEvent.wait()
                # Set the name and time attributes while the function is executing
                self.server.CurrentCmd_RxTime = rxTime
                self.server.CurrentCmd_ClientName = client
                try:
                    if self.server.ServerKillRequested:
                        raise KillInProgress(
                            "RPC aborted because server has been killed")
                    else:
                        return func(*a, **k)
                finally:
                    self.eventLock.acquire()
                    self.queueLength -= 1
                    # print "Removing blocking method %s from queue, length %d" % (method,self.queueLength)
                    self.eventLock.release()
                    # Allow next function to run by setting its event
                    nextEvent.set()

            # Execute Callback mode functions in VerifyOnly mode, if no callback
            #  info is available
            elif funcMode == CMD_TYPE_VerifyOnly or callbackInfo == None:
                def __waitAndDispatch():
                    """This function is executed within a daemonic thread at the
                    correct time, because it waits on the appropriate event."""
                    myEvent.wait()
                    # Set the name and time attributes while the function is executing
                    self.server.CurrentCmd_RxTime = rxTime
                    self.server.CurrentCmd_ClientName = client
                    try:
                        if not self.server.ServerKillRequested:
                            func(*a, **k)
                    finally:
                        self.eventLock.acquire()
                        self.queueLength -= 1
                        # print "Removing blocking method %s from queue, length %d" % (method,self.queueLength)
                        self.eventLock.release()
                        # Allow next function to run by setting its event
                        nextEvent.set()
                DaemonicThread(target=__waitAndDispatch).start()
                return "OK"

            else:  # funcMode == CMD_TYPE_Callback
                uri, callbackName = callbackInfo
                m = uriRegex.match(uri)
                if m:
                    address = m.group(1)
                    port = int(m.group(2))
                else:
                    raise ValueError(
                        "Invalid callback URI %s (should be http://address:port)" % uri)

                # Set the name and time attributes while the function is executing
                self.server.CurrentCmd_RxTime = rxTime
                self.server.CurrentCmd_ClientName = client

                def __waitDispatchAndCallback():
                    """This function is executed within a daemonic thread at the
                    correct time, because it waits on the appropriate event. After
                    the function finishes, issue the callback."""
                    myEvent.wait()
                    result = None
                    faultString = ""
                    try:
                        if self.server.ServerKillRequested:
                            raise KillInProgress(
                                "RPC aborted because server has been killed")
                        else:
                            result = func(*a, **k)
                    except Exception as exc:
                        faultString = "%s:%s" % (repr(exc), str(exc))
                    try:
                        while True:
                            # Loop around in case the callback server has gone down
                            #  and come up again
                            try:
                                callbackObject = Pyro4.core.Proxy(
                                    "PYRO:callbackObject@%s:%d" % (address, port))
                                callbackObject._pyroOneway.add("__dispatch__")
                                callbackObject.__dispatch__(
                                    callbackName, (result, faultString), {})
                                break
                            except Pyro4.errors.ConnectionClosedError:
                                pass
                    finally:
                        self.eventLock.acquire()
                        self.queueLength -= 1
                        # print "Removing blocking method %s from queue, length %d" % (method,self.queueLength)
                        self.eventLock.release()
                        # Allow next function to run by setting its event
                        nextEvent.set()
                DaemonicThread(target=__waitDispatchAndCallback).start()
                return "CB"

    def __init__(self, addr, ServerName, requestHandler=None,
                 logRequests=False, threaded=True, DumpToStdout=False,
                 ServerDescription="", ServerVersion="", LogFunc=None):
        """Creates a CmdFIFOServer. Parameters are:
            addr:              (hostName,port) tuple for server
            ServerName:        string identifying the server
            logRequests:       set to True to enable RPC calls to be logged
            DumpToStdout:      set to True to direct log to stdout
            ServerDescription: descriptive string for server
            ServerVersion:     version string for server
            LogFunc:           If not None, Log entries are sent to this function

            The legacy parameters threaded and requestHandler are not used and have
             no effect.
        """
        # Logging is enabled if DumpToStdout is True, or if a LogFunc is specified.
        #  Use the Python logging module with a unique logger name for each
        #  CmdFIFOServer instance
        self.logger = None
        if DumpToStdout or LogFunc != None:
            self.logger = logging.getLogger("%d" % CmdFIFOServer.loggerInst)
            self.logger.setLevel(level=logging.INFO)
            CmdFIFOServer.loggerInst += 1

        if LogFunc != None:
            # If a LogFunc is specified, entries to a stream object have to be passed
            #  to this function. The following class provides this feature.
            class LogStream(object):
                def write(self, x):
                    LogFunc(x)

                def flush(self):
                    pass
            # No formatter is used, so logging data are passed directly to LogFunc
            logFuncHandle = logging.StreamHandler(LogStream())
            logFuncHandle.setLevel(level=logging.INFO)
            self.logger.addHandler(logFuncHandle)

        if DumpToStdout:
            # Deal with logging to stdout
            formatter = logging.Formatter(
                '%(asctime)s %(message)s', datefmt='%H:%M:%S')
            stdoutHandle = logging.StreamHandler(sys.stdout)
            stdoutHandle.setFormatter(formatter)
            stdoutHandle.setLevel(level=logging.INFO)
            self.logger.addHandler(stdoutHandle)

        self.thread = None
        self.logRequests = logRequests

        # Variables used by other applications which can monitor the state of the server
        self.CurrentCmd_RxTime = -1  # can be used by RPC implementations if needed
        self.CurrentCmd_ClientName = "__NO_ACTIVE_COMMAND__"
        self.ServerStopRequested = False
        self.ServerKillRequested = False

        self.serverName = ServerName
        self.serverDescription = ServerDescription
        self.serverVersion = ServerVersion
        self.hostName, self.port = addr
        self.pyroDaemon = Pyro4.core.Daemon(host=self.hostName, port=self.port)
        self.daemon = DummyDaemon(self.pyroDaemon)
        if self.logger:
            self.logger.info("CmdFIFO %s started" % self.serverName)
        # The serverObject and calbackObject are the targets of all the RPC calls. Their
        #  activity is carried out in their __dispatch__ methods.
        self.serverObject = CmdFIFOServer.ServerObject(self)
        self.callbackObject = CmdFIFOServer.CallbackObject(self)
        # Register these objects will well-known names
        self.pyroDaemon.register(self.serverObject, "serverObject")
        self.pyroDaemon.register(self.callbackObject, "callbackObject")
        # Register built-in functions for the server
        self._register_cmdfifo_functions()

    def handle_requests(self, *a, **k):
        # Delegate to DummyDaemon for compatibility with Pyro3
        self.daemon.handleRequests(*a, **k)

    def Launch(self):
        """Starts the server service loop within a daemonic thread"""
        self.thread = DaemonicThread(target=self.serve_forever)
        self.thread.start()

    def serve_forever(self, timeout=0.5):
        """Calls the service loop function. This may be broken using the shutdown method
        of the daemon"""
        self.running = True
        while self.running:
            self.handle_requests(timeout=timeout)
        if self.pyroDaemon is not None:
            self.pyroDaemon.close()
            self.pyroDaemon = None

    def Stop(self):
        """Stops the thread running the server main loop, and wait for it to terminate"""
        self.stop_server()
        if self.thread != None:
            self.thread.join()
            self.thread = None

    def stop_server(self):
        """Stops the service loop of the daemon, and delete the daemon so that the server
        port is released for future connections"""
        self.running = False
        self.daemon.mustShutdown = True
        if self.logger:
            self.logger.info("CmdFIFO %s terminated" % self.serverName)

    def _CmdFIFO_GetDescription(self):
        """Gets the description of the rpc server."""
        return self.serverDescription

    def _CmdFIFO_GetName(self):
        """Gets the name of the rpc server."""
        return self.serverName

    def _CmdFIFO_GetProcessID(self):
        """Gets the os process ID of the process using the CmdFIFO class."""
        return os.getpid()

    def _CmdFIFO_GetQueueLength(self):
        """Returns the number of commands currently in the FIFO queue."""
        return self.serverObject.queueLength

    def _CmdFIFO_GetVersion(self):
        """Gets the version of the rpc server."""
        return self.serverVersion

    @rpc_wrap
    def _CmdFIFO_DebugDelay(self, sec):
        if sec > 0:
            time.sleep(sec)
        else:
            raise ValueError("Invalid delay: %s" % sec)

    def _CmdFIFO_KillServer(self, password):
        """Stops the server immediately"""
        if password == "please":
            self.ServerKillRequested = True
            self.stop_server()
        else:
            raise CmdFIFOError("Invalid password for KillServer")
        return "OK"

    def _CmdFIFO_PingDispatcher(self):
        """Immediately returns the string "Ping OK", bypassing the FIFO"""
        return "Ping OK"

    def _CmdFIFO_PingFIFO(self):
        """Enqueues a function that returns "Ping OK" on the FIFO"""
        return "Ping OK"

    def _CmdFIFO_StopServer(self):
        """Stops the server once all entries in queue have completed"""
        self.stop_server()

    def system_listMethods(self):
        """system.listMethods() => ['add', 'subtract', 'multiple']

        Returns a list of the methods supported by the server."""

        methods = list(self.serverObject.funcs.keys())
        if self.serverObject.instance is not None:
            # Instance can implement _listMethod to return a list of
            # methods
            if hasattr(self.serverObject.instance, '_listMethods'):
                methods = remove_duplicates(
                    methods + self.serverObject.instance._listMethods()
                )
            # if the instance has a __dispatch__ method then we
            # don't have enough information to provide a list
            # of methods
            elif not hasattr(self.serverObject.instance, '__dispatch__'):
                methods = remove_duplicates(
                    methods + list_public_methods(self.serverObject.instance)
                )
        methods.sort()
        return methods

    def system_methodSignature(self, method_name):
        """system.methodSignature('add') => (x,y)

        Returns a string containing the argument list for the method, with
        optionals wrapped in square brackets."""

        if method_name not in self.serverObject.funcs:
            return "%s method not found" % method_name
        f = self.serverObject.funcs[method_name]
        argCount = getattr(f, "__wrapped_co_argcount", f.__code__.co_argcount)
        optionalCount = 0
        defaults = getattr(f, "__wrapped_defaults", f.__defaults__)
        if defaults:
            optionalCount = len(defaults)

        if argCount == 0:
            ret = ''
        else:
            varNames = getattr(f, "__wrapped_co_varnames",
                               f.__code__.co_varnames)
            args = list(varNames)[:argCount]
            # wrap the optionals in square brackets...
            if optionalCount > 0:
                args[-optionalCount:] = ["[%s]" %
                                         (s,) for s in args[-optionalCount:]]
            ret = '(' + ', '.join(args[:argCount]) + ')'
        return ret

    def system_methodHelp(self, method_name):
        """system.methodHelp('add') => "Adds two integers together"

        Returns a string containing documentation for the specified method."""

        method = None
        if method_name in self.serverObject.funcs:
            method = self.serverObject.funcs[method_name]
        elif self.serverObject.instance is not None:
            # Instance can implement _methodHelp to return help for a method
            if hasattr(self.serverObject.instance, '_methodHelp'):
                return self.serverObject.instance._methodHelp(method_name)
            # if the instance has a __dispatch__ method then we
            # don't have enough information to provide help
            elif not hasattr(self.serverObject.instance, '__dispatch__'):
                try:
                    method = resolve_dotted_attribute(
                        self.serverObject.instance,
                        method_name,
                        self.serverObject.allow_dotted_names
                    )
                except AttributeError:
                    pass

        # Note that we aren't checking that the method actually
        # be a callable object of some kind
        if method is None:
            return "%s method not found" % method_name
        else:
            return getattr(method, "__wrapped_doc", pydoc.getdoc(method))

    def register_function(self, function, name=None, DefaultMode=CMD_TYPE_Blocking, NameSlice=0, EscapeDoubleUS=False):
        """Registers a function to respond to RPC requests.

        The optional name argument can be used to set a name
        for the function.
        """
        if name is None:
            name = function.__name__
        if NameSlice > 0:
            name = name[NameSlice:]
        elif NameSlice < 0:
            name = name[:NameSlice]
        if not EscapeDoubleUS:
            name = name.replace("__", ".")
        self.serverObject.funcs[name] = function
        self.serverObject.funcModes[name] = DefaultMode
        return name

    def register_callback_function(self, function, name=None, NameSlice=0):
        """Registers a callback function.  Callbacks are unique from regular functions.

        - Callbacks must be defined in the following way:
            def CallbackName(ReturnedVars, Fault):

        It is important to remember that callback functions are priority
        functions, which means that they skip the command queue. ie: callback
        functions should be VERY quick and have no chance of being a blocking
        call. The best thing to do with a callback is simply to set a flag
        variable that your main application will be looking for.

        """
        # do some verification on the declaration...
        codeObj = function.__code__
        # Allow for functions and methods as callbacks
        if (isinstance(function, types.MethodType) and codeObj.co_argcount != 3) or \
                (not isinstance(function, types.MethodType) and codeObj.co_argcount != 2):
            argList = codeObj.co_varnames[:codeObj.co_argcount]
            errMsg = "Callback functions must have exactly two arguments [excluding self].  Attempted argList: %r" % (
                argList,)
            raise CmdFIFOError(errMsg)
        else:
            if name is None:
                name = function.__name__
            if NameSlice > 0:
                name = name[NameSlice:]
            elif NameSlice < 0:
                name = name[:NameSlice]
            self.callbackObject.funcs[name] = function
            # print "Callback function %s registered" % (name,)

    def register_instance(self, instance, allow_dotted_names=False):
        """Registers an instance to respond to RPC requests.

        Only one instance can be installed at a time. Instance
        mthods are always called with CMD_TYPE_Blocking as the
        default FIFO mode.

        If the registered instance has a __dispatch__ method then that
        method will be called with the name of the RPC method and
        its parameters as a tuple
        e.g. instance.__dispatch__('add',(2,3))

        If the registered instance does not have a __dispatch__ method
        then the instance will be searched to find a matching method
        and, if found, will be called. Methods beginning with an '_'
        are considered private and will not be called by
        CmdFIFOServer.

        If a registered function matches a RPC request, then it
        will be called instead of the registered instance.

        If the optional allow_dotted_names argument is true and the
        instance does not have a __dispatch__ method, method names
        containing dots are supported and resolved, as long as none of
        the name segments start with an '_'.

            *** SECURITY WARNING: ***

            Enabling the allow_dotted_names options allows intruders
            to access your module's global variables and may allow
            intruders to execute arbitrary code on your machine.  Only
            use this option on a secure, closed network.

        """
        self.serverObject.instance = instance
        self.serverObject.allow_dotted_names = allow_dotted_names

    def _register_priority_function(self, function, name=None,
                                    DefaultMode=CMD_TYPE_VerifyOnly,
                                    NameSlice=0):
        """Registers a function so that it is immediately executed by the dispatcher.

        Priority functions need not be entered into a queue but are immediately executed.

        DefaultMode is not actually used (the modes only apply to serialized execution).
        It is being kept here purely for legacy reasons to avoid a code change.
        """
        registeredName = self.register_function(
            function, name, DefaultMode, NameSlice=NameSlice)
        self.serverObject.priorityFunctions.append(registeredName)

    def _register_cmdfifo_functions(self):
        """Registers the built-in functions for the CmdFIFO"""
        # register the 'standard' introspection functions...
        self._register_priority_function(
            self.system_listMethods, 'system.listMethods', CMD_TYPE_Blocking)
        self._register_priority_function(
            self.system_methodSignature, 'system.methodSignature', CMD_TYPE_Blocking)
        self._register_priority_function(
            self.system_methodHelp, 'system.methodHelp', CMD_TYPE_Blocking)

        # register some CmdFIFO specific RPCs...
        self.register_function(self._CmdFIFO_PingFIFO,
                               'CmdFIFO.PingFIFO', CMD_TYPE_Blocking)
        self._CmdFIFO_StopServer = self.stop_server  # alias
        self.register_function(self._CmdFIFO_StopServer,
                               'CmdFIFO.StopServer', CMD_TYPE_VerifyOnly)
        self.register_function(self._CmdFIFO_DebugDelay,
                               'CmdFIFO.DebugDelay', CMD_TYPE_Blocking)

        # register some priority CmdFIFO RPCs (that don't need to wait in the FIFO queue)...
        self._register_priority_function(
            self._CmdFIFO_PingDispatcher, 'CmdFIFO.PingDispatcher', CMD_TYPE_Blocking)
        self._register_priority_function(
            self._CmdFIFO_KillServer, 'CmdFIFO.KillServer', CMD_TYPE_VerifyOnly)
        self._register_priority_function(
            self._CmdFIFO_GetProcessID, 'CmdFIFO.GetProcessID', CMD_TYPE_Blocking)
        self._register_priority_function(
            self._CmdFIFO_GetQueueLength, 'CmdFIFO.GetQueueLength', CMD_TYPE_Blocking)
        self._register_priority_function(
            self._CmdFIFO_GetName, 'CmdFIFO.GetName', CMD_TYPE_Blocking)
        self._register_priority_function(
            self._CmdFIFO_GetDescription, 'CmdFIFO.GetDescription', CMD_TYPE_Blocking)
        self._register_priority_function(
            self._CmdFIFO_GetVersion, 'CmdFIFO.GetVersion', CMD_TYPE_Blocking)


class CmdFIFOSimpleCallbackServer(object):
    """Macro class to use when ONLY setting up a callback server.

    NOTE: If the application where you intend to set up a callback already has a
    CmdFIFOServer listening on a port, there is NO NEED to set up an additional
    server and thus needing to allocate another port #. All that need be done is
    register the callback functions you want with the use of the
    register_callback_function method of CmdFIFOServer. See the docs for that
    call for directions how to do this.

    It is important to remember that callback functions are priority functions
    so they skip the command queue. ie: callback functions should be VERY quick
    and have no chance of being a blocking call. The best thing to do with a
    callback is simply to set a flag variable that your main application will be
    looking for.

    If you do wish to set up a server for callbacks only (eg: if you are writing
    a client-only application) you can use this class.

    To use this class, first define some functions that meet the requirements for
    a callback (see CmdFIFOServer.register_callback_function docs) and then make
    a tuple out of the function you want to be callbacks (the actual objects, not
    the names).  This tuple is then to be passed to the CallbackList argument
    of the constructor (yes - it is a bad arg name, and reasons for it being a
    tuple are historic).
    """

    def __init__(self, addr, threaded=True, DumpToStdout=False, CallbackList=None, **kwargs):
        self.thread = None
        self.server = CmdFIFOServer(
            addr, "CBServer", threaded=threaded, DumpToStdout=DumpToStdout, **kwargs)
        self.Server = self.server  # Legacy name for compatibility
        if CallbackList != None:
            assert isinstance(
                CallbackList, tuple), "Contrary to the name, this arg should be a tuple"
            for func in CallbackList:
                self.server.register_callback_function(func)

    def handle_requests(self, *a, **k):
        self.server.handle_requests(*a, **k)

    def Launch(self):
        self.thread = DaemonicThread(
            target=self.server.serve_forever, kwargs=dict(timeout=.1))
        self.thread.start()

    def serve_forever(self, *a, **k):
        self.server.serve_forever(*a, **k)

    def Stop(self):
        self.server.stop_server()
        if self.thread != None:
            self.thread.join()
            self.thread = None

    def stop_server(self, *a, **k):
        self.server.stop_server(*a, **k)


class CmdFIFOServerProxy(object):
    def __init__(self, uri, ClientName, CallbackURI="",
                 IsDontCareConnection=False, Timeout_s=None):
        """Called by the client to create a proxy object which may be called to
            execute code on a CmdFIFOServer. Parameters are:
            uri:                  "http://address:port" string specifying the server
            ClientName:           string identifying the client
            CallbackURI:          "http://address:port" string specifying the callback
                                    server which runs on the client
            IsDontCareConnection: set to True to make all calls non-blocking. Functions
                                    are run in daemonic threads and no errors are
                                    raised even if the server does not exist
            Timeout_s:            used to specify a timeout, after which a TimeoutError
                                    is raised if no response is received
        """
        self.ClientName = ClientName
        # should be "http://address:port".  eg: "http://localhost:8000"
        self.CallbackURI = CallbackURI.lower()
        self.IsDontCare = IsDontCareConnection
        # Following dictionaries are used by SetFunctionMode to specify that
        #  certain functions should be treated specially
        self._FuncModes = {}
        self._FuncCallbacks = {}
        self.uri = uri.lower()
        self.timeout = Timeout_s
        self.setupRemoteObject()

    def setupRemoteObject(self):
        m = uriRegex.match(self.uri)
        if m:
            address = m.group(1)
            port = int(m.group(2))
        else:
            raise ValueError(
                "Invalid RPC server URI %s (should be http://address:port)" % self.uri)
        self.remoteObject = Pyro4.core.Proxy(
            "PYRO:serverObject@%s:%d" % (address, port))
        self.setup = True
        self.SetTimeout(self.timeout)
        # Use Oneway function, if we do not care about the result
        if self.IsDontCare:
            self.remoteObject._pyroOneway.add("__dispatch__")
        else:
            self.remoteObject._pyroOneway.clear()

    def __getattr__(self, name):
        # Suppose that the proxy is called as proxy.system.test.func. This __getattr__ function
        #  will be called with "name" set to "system". It returns an object whose __call__ method
        #  is defined, so that when it is applied to a list of arguments, the effect is to
        #  execute self.applyRemoteFunction("system.test.func",positional args-tuple,kwd args-dict)
        return _Method(self.applyRemoteFunction, name)

    def applyRemoteFunction(self, dottedMethodName, a, k):
        # Calls the __dispatch__ function of the remote object to apply a method
        #  to some arguments.
        # The additional parameters client, modeOverride and callbackInfo are
        #  also sent to the remote object
        # print("Calling remote function")
        client = self.ClientName
        modeOverride = CMD_TYPE_Default
        callbackInfo = None
        if dottedMethodName in self._FuncModes:
            modeOverride = self._FuncModes[dottedMethodName]
        if dottedMethodName in self._FuncCallbacks:
            callbackInfo = (self.CallbackURI,
                            self._FuncCallbacks[dottedMethodName].__name__)
        # If the function is to be executed in VerifyOnly or Callback modes,
        #  or if the proxy is in don't care mode, we send off the request
        #  in a thread
        if self.IsDontCare or modeOverride in ["V", "C"]:
            if not self.setup:
                try:
                    self.setupRemoteObject()
                except Pyro4.errors.ProtocolError:
                    self.setup = False
            if self.setup:
                def curried():
                    try:
                        self.remoteObject.__dispatch__(
                            dottedMethodName, client, modeOverride, callbackInfo, a, k)
                    except:
                        self.setup = False
                DaemonicThread(target=curried).start()
            if self.IsDontCare:
                return "DC"
            elif modeOverride == "V":
                return "OK"
            else:
                return "CB"
        else:
            for _ in range(2):
                # Perform command and re-establish connection if necessary
                if self.setup:
                    try:
                        return self.remoteObject.__dispatch__(dottedMethodName, client, modeOverride, callbackInfo, a, k)
                    except Pyro4.errors.TimeoutError as e:
                        raise TimeoutError("%s" % e)
                    except Pyro4.errors.ConnectionClosedError:
                        pass
                        # print "Retrying proxy call: %s" % (dottedMethodName,)
                time.sleep(0.5)
                try:
                    self.setupRemoteObject()
                except Pyro4.errors.ProtocolError:
                    self.setup = False
            raise RemoteException("Remote cannot be reached for RPC")

    def SetFunctionMode(self, FuncName, FuncMode=CMD_TYPE_Default, Callback=None):
        """Sets how the client would like a registered server function to behave.

        You must be very careful to get the FuncName reference right.  It must
        match the server naming exactly.  There is no error trapping for incorrect
        naming with this call (this checking could be implemented by using
        introspection features on the server, but then the client would be reliant
        on the server being alive, which may not be the case and we don't want
        the client to be brought down unnecessarily.
        """
        if not FuncMode in CMD_Types:
            raise CmdFIFOError("CMD_Type '%s' does not exist." % FuncMode)
        else:
            self._FuncModes[FuncName] = FuncMode
        if FuncMode == CMD_TYPE_Callback:
            if callable(Callback):
                self._FuncCallbacks[FuncName] = Callback
            else:
                raise CmdFIFOError(
                    "Callback argument must be a callable function (not just the name).")
        else:
            if Callback != None:
                raise CmdFIFOError(
                    "Unexpected Callback argument since FuncMode != CMD_Type_Callback.")

    def SetTimeout(self, sec):
        """Set the socket timeout for the proxy. Use None to remove timeout"""
        self.timeout = sec
        # print(sec)
        if sec is None:
            Pyro4.config.COMMTIMEOUT = 0.0
        else:
            print('gets here')
            Pyro4.config.AUTOPROXY = True
            Pyro4.config.COMMTIMEOUT = sec

    def GetTimeout(self):
        """Gets the socket timeout for the proxy."""
        return self.timeout


class _Method:
    # some magic to bind an XML-RPC method to an RPC server.
    # supports "nested" methods (e.g. examples.getStateName)
    def __init__(self, send, name):
        self.__send = send
        self.__name = name

    def __getattr__(self, name):
        return _Method(self.__send, "%s.%s" % (self.__name, name))

    def __call__(self, *args, **kwargs):
        return self.__send(self.__name, args, kwargs)
