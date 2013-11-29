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

from chimera.core.rpc import RedisRpc
from chimera.core.jsonrpc import Request

log = logging.getLogger(__name__)

__all__ = ['EventsProxy']


class EventsProxy:

    def __init__(self):
        self.rpc = RedisRpc("localhost", 6379)
        self.handlers = {}

    def subscribe (self, topic, handler):
        if topic not in self.handlers:
            self.handlers[topic] = []

        if handler not in self.handlers[topic]:
            self.handlers[topic].append(handler)

        return True

    def unsubscribe (self, topic, handler):
        if not topic in self.handlers:
            return True

        if handler not in self.handlers[topic]:
            return True

        self.handlers[topic].remove(handler)

        return True

    def publish (self, topic, *args, **kwargs):
        if topic not in self.handlers:
            return True

        for handler in self.handlers[topic]:
            request = Request()
            request.id = None
            request.method = handler["method"]
            request.params = [args, kwargs]

            self.rpc.send(handler["id"], request)

        return True
