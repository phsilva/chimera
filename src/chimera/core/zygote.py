import multiprocessing
import signal
import traceback
import setproctitle

import concurrent.futures

from chimera.core.rpc import RedisRpc
from chimera.core.jsonrpc import Request, Response
from chimera.core.classloader import ClassLoader


def multi_getattr(obj, attr, default = None):
    """
    Get a named attribute from an object; multi_getattr(x, 'a.b.c.d') is
    equivalent to x.a.b.c.d. When a default argument is given, it is
    returned when any attribute in the chain doesn't exist; without
    it, an exception is raised when a missing attribute is encountered.

    """
    attributes = attr.split(".")
    for i in attributes:
        try:
            obj = getattr(obj, i)
        except AttributeError:
            if default:
                return default
            else:
                raise
    return obj


class ZygoteProcess(object):

    def __init__(self, location):
        self.location = location

        # identity
        setproctitle.setproctitle("[%s]" % self.location)

        # ignore ctrl-c
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        # load class
        loader = ClassLoader()
        cls = loader.loadClass(self.location.cls)

        # create object (lives in zygote process)
        self.obj = cls()

        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=16)
        self.rpc = RedisRpc(self.location.host or "localhost", self.location.port or 6379)
        self.requests = {}

        # set object identify
        self.obj.__setlocation__(self.location)

    def run(self):
        # objects main loop
        # FIXME: general event log if something goes wrong with this guy?        
        main_future = self.pool.submit(self.obj.__main__)

        # request/reply loop
        while True:
            _, buff = self.rpc.recv(self.location)
            request = None

            try:
                request = Request.fromBuffer(buff)
            except Exception, e:
                # TODO:how to inform requester that a parser error occured?
                continue

            future = self.pool.submit(self.process_request, request=request)

            # do this first, cause callback might be called immediately if request already finished
            self.requests[future] = request

            # this will send server exceptions that might occur on request execution
            # application exceptions are handled inside process_request
            future.add_done_callback(self.request_finished)

            if request.method == "__stop__":
                break

        # quit control loop first
        self.obj.__abort_loop__()

        # then quit any pending requests
        self.pool.shutdown(wait=True)

    def process_request(self, request):
        # consume and execute commands
        rpc = RedisRpc(self.location.host or "localhost",
                       self.location.port or 6379)
        result = None
        error = None

        try:
            method = multi_getattr(self.obj, request.method)
            args, kwargs = request.params            
            result = method(*args, **kwargs)
        except Exception, e:
            error = {"exc_cause": traceback.format_exc()}

        if request.id is not None:
            response = Response.fromParams(request.id, result, error)
            rpc.send(response.id, response)

        return True

    def request_finished(self, future):
        # check for server-side exceptions
        exc = future.exception()
        if exc:
            rpc = RedisRpc(self.location.host or "localhost", self.location.port or 6379)
            request = self.requests[future]

            if request.id is not None:
                response = Response.fromParams(request.id, None, {"exc_cause": str(exc)})
                rpc.send(response.id, response)

        del self.requests[future]

def zygote(location):
    zygo_proc = ZygoteProcess(location)
    zygo_proc.run()


class Zygote:

    def __init__(self, location):
        self.process = None
        self.location = location

    def start(self):
        self.process = multiprocessing.Process(target=zygote,args=(self.location,))
        self.process.start()

    def stop(self):
        self.process.join()

