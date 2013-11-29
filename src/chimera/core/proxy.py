#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import logging
import uuid

from chimera.core.rpc import RedisRpc
from chimera.core.jsonrpc import Request, Response
from chimera.core.resources import ResourceManager
from chimera.core.location import Location
from chimera.core.constants import EVENTS_PROXY_NAME

__all__ = ['Proxy',
           'ProxyMethod']

log = logging.getLogger(__name__)

def call_random_id(location):
    return str(location) + "#" + str(uuid.uuid4())

class Proxy:

    def __init__ (self, location):
        if not isinstance(location, Location):
            location = Location(location)

        self.location = location
        self.resolved = False

        self.rpc = RedisRpc(location.host or "localhost",
                            location.port or 6379)

    def __getattr__ (self, attr):
        return ProxyMethod(self, attr)

    def __iadd__ (self, configDict):
        ProxyMethod(self, "__iadd__")(configDict)
        return self

    def __repr__ (self):
        return "<%s proxy at %s>" % (self.location, hex(id(self)))

    def __str__ (self):
        return "[proxy for %s]" % self.location

class ProxyMethod (object):

    def __init__ (self, proxy, method):
        self.proxy  = proxy
        self.method = method

        self.__name__ = method

    def __repr__ (self):
        return "<%s.%s method proxy at %s>" % (self.proxy.location,
                                               self.method,
                                               hex(hash(self)))

    def __str__ (self):
        return "[method proxy for %s %s method]" % (self.proxy.location,
                                                    self.method)

    # synchronous call
    def __call__ (self, *args, **kwargs):
        return self.__sync_dispatcher__(*args, **kwargs)

    def __sync_dispatcher__(self, *args, **kwargs):
        if not self.proxy.resolved:
            resources = ResourceManager(self.proxy.location.host or "localhost",
                                        self.proxy.location.port or 6379)

            self.proxy.location = resources.get(self.proxy.location).location
            self.proxy.resolved = True

        request = Request()
        request.id = call_random_id(self.proxy.location)
        request.method = self.method
        request.params = [args, kwargs]

        self.proxy.rpc.send(self.proxy.location, request)

        _, buff = self.proxy.rpc.recv(request.id)

        # discard request queue as it will not be reused, could use expire, but what is the right (tm) timeout?
        self.proxy.rpc.redis.delete(request.id)

        response = Response.fromBuffer(buff)
        return response.result

    # event handling
    def __iadd__(self, proxy_method):
        """
        @type proxy_method: ProxyMethod
        """
        return self.__event_dispatcher__(proxy_method, "subscribe")

    def __isub__(self, proxy_method):
        """
        @type proxy_method: ProxyMethod
        """
        return self.__event_dispatcher__(proxy_method, "unsubscribe")

    def __event_dispatcher__(self, callback, action):
        """
        @type callback: ProxyMethod
        @type action: str
        """
        # Can't add itself as a subscriber
        if callback == self:
            return self

        # passing a proxy method?
        if not isinstance (callback, ProxyMethod):
            log.debug("Invalid parameter: %s" % callback)
            raise TypeError("Invalid parameter: %s" % callback)

        kwargs = {"topic": self.method, "handler": {"id": str(callback.proxy.location), "method": callback.method}}

        request = Request()
        request.id = call_random_id(self.proxy.location)
        request.method = "%s.%s" % (EVENTS_PROXY_NAME, action)
        request.params = [[], kwargs]

        self.proxy.rpc.send(self.proxy.location, request)

        _, buff = self.proxy.rpc.recv(request.id)

        # discard request queue as it will not be reused, could use expire, but what is the right (tm) timeout?
        self.proxy.rpc.redis.delete(request.id)

        return self

