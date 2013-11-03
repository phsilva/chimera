import redis as R

__author__ = 'ph'


class RedisRpc:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.redis = R.StrictRedis(self.host, self.port)

    def send(self, queue, data):
        return self.redis.rpush(queue, data)

    def recv(self, queue):
        return self.redis.blpop(queue)