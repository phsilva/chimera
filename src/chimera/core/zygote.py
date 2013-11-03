import multiprocessing
import setproctitle

from chimera.core.rpc import RedisRpc
from chimera.core.jsonrpc import Request, Response
from chimera.core.classloader import ClassLoader

def zygote(resource):
    # identity
    setproctitle.setproctitle("[%s]" % resource.location)

    # load class
    loader = ClassLoader()
    cls = loader.loadClass(resource.location.cls)

    # create object (lives in zygote process)
    obj = cls()

    # consume and execute commands
    rpc = RedisRpc(resource.location.host or "localhost",
                   resource.location.port or 6379)

    while True:
        _, buff = rpc.recv(resource.uuid)
        request = Request.fromBuffer(buff)

        method = getattr(obj, request.method)
        args, kwargs = request.params

        result = None
        error = None

        try:
            result = method(*args, **kwargs)
        except Exception, e:
            error = e

        response = Response.fromParams(request.id, result, error)
        rpc.send(response.id, str(response))

class Zygote:

    def __init__(self, resource):
        self.process = None
        self.resource = resource

    def start(self):
        self.process = multiprocessing.Process(target=zygote,args=(self.resource,))
        self.process.start()

    def stop(self):
        self.process.join()

