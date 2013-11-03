import jsonpickle

class Request(object):

    @staticmethod
    def fromParams(method, params={}, id=None):
        request = Request
        request.method = method
        request.params = params
        request.id = id
        return request

    @staticmethod
    def fromBuffer(buff):
        d = jsonpickle.decode(buff)

        request = Request()
        request.method = d.get("method", None)
        request.params = d.get("params", {})
        request.id = d.get("id", None)
        return request

    jsonrpc = "2.0"
    id = None
    method = None
    params = {}

    def __str__(self):
        return jsonpickle.encode(self.__dict__)

class Response(object):

    id = None
    result = {}
    error = {}

    @staticmethod
    def fromParams(id, result={}, error={}):
        response = Response()
        response.id = id
        response.result = result
        response.error = error
        return response

    @staticmethod
    def fromBuffer(buff):
        d = jsonpickle.decode(buff)

        response = Response()
        response.id  = d.get("id", None)
        response.result = d.get("result", {})
        response.error = d.get("error", {})
        return response

    def __str__(self):
        return jsonpickle.encode(self.__dict__)
