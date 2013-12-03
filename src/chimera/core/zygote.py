import multiprocessing

import signal
import traceback
import setproctitle

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

def zygote(resource):
    # identity
    setproctitle.setproctitle("[%s]" % resource.location)

    # ignore ctrl-c
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # load class
    loader = ClassLoader()
    cls = loader.loadClass(resource.location.cls)

    # create object (lives in zygote process)
    obj = cls()

    # set object identify
    obj.__setlocation__(resource.location)

    # consume and execute commands
    rpc = RedisRpc(resource.location.host or "localhost",
                   resource.location.port or 6379)

    while True:
        _, buff = rpc.recv(resource.location)
        request = Request.fromBuffer(buff)

        method = multi_getattr(obj, request.method)
        args, kwargs = request.params

        result = None
        error = None

        try:
            result = method(*args, **kwargs)
        except Exception, e:
            error = {"exc_type": type(e), "exc_value": e, "exc_traceback": traceback.format_exc()}

        if request.id is not None:
            response = Response.fromParams(request.id, result, error)
            rpc.send(response.id, response)

        if request.method == "__stop__":
            break

class Zygote:

    def __init__(self, resource):
        self.process = None
        self.resource = resource

    def start(self):
        self.process = multiprocessing.Process(target=zygote,args=(self.resource,))
        self.process.start()

    def stop(self):
        self.process.join()

