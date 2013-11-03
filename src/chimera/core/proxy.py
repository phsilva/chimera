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
from chimera.core.exceptions import ChimeraException

__all__ = ['Proxy',
           'ProxyMethod']

log = logging.getLogger(__name__)
           
class Proxy:

    def __init__ (self, location):
        if not isinstance(location, Location):
            location = Location(location)

        self.location = location
        self.location_uuid = None

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
        if self.proxy.location_uuid is None:
            resources = ResourceManager(self.proxy.location.host or "localhost",
                                        self.proxy.location.port or 6379)
            self.proxy.location_uuid = resources.get(self.proxy.location).uuid

        request = Request()
        request.id = self.proxy.location_uuid + "_" + str(uuid.uuid4())
        request.method = self.method
        request.params = [args, kwargs]

        self.proxy.rpc.send(self.proxy.location_uuid, str(request))

        _, buff = self.proxy.rpc.recv(request.id)

        response = Response.fromBuffer(buff)
        if response.error is None:
            return response.result
        else:
            raise ChimeraException("pqp")

    # async pattern
    #def begin (self, *args, **kwargs):
    #    return self.dispatcher("%s.begin" % self.method, args, kwargs)
    #
    #def end (self, *args, **kwargs):
    #    return self.dispatcher("%s.end" % self.method, args, kwargs)

    # event handling
    #def __do (self, other, action):
    #
    #    handler = {"topic"    : self.method,
    #               "handler"  : {"proxy" : "", "method": ""}}
    #
    #    # REMEBER: Return a copy of this wrapper as we are using +=
    #
    #    # Can't add itself as a subscriber
    #    if other == self:
    #        return self
    #
    #    # passing a proxy method?
    #    if not isinstance (other, ProxyMethod):
    #        log.debug("Invalid parameter: %s" % other)
    #        raise TypeError("Invalid parameter: %s" % other)
    #
    #    handler["handler"]["proxy"] = other.proxy.location
    #    handler["handler"]["method"] = str(other.__name__)
    #
    #    try:
    #        self.dispatcher("%s.%s" % (EVENTS_PROXY_NAME, action), (handler,), {})
    #    except Exception, e:
    #        log.exception("Cannot %s to topic '%s' using proxy '%s'." % (action,
    #                                                                     self.method,
    #                                                                     self.proxy))
    #
    #    return self
    #
    #def __iadd__ (self, other):
    #    return self.__do (other, "subscribe")
    #
    #def __isub__ (self, other):
    #    return self.__do (other, "unsubscribe")
