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


from chimera.core.proxy          import ProxyMethod
from chimera.core.methodwrapper  import MethodWrapperDispatcher

from chimera.core.constants import EVENTS_PROXY_NAME

__all__ = ['EventWrapperDispatcher']


class EventWrapperDispatcher(MethodWrapperDispatcher):   

    def __init__(self, wrapper, instance, cls):
        MethodWrapperDispatcher.__init__(self, wrapper, instance, cls)

    def call(self, *args, **kwargs):
        proxy = getattr(self.instance, EVENTS_PROXY_NAME)
        proxy.publish(self.func.__name__, *args[1:], **kwargs)
        return True

    def __iadd__(self, other):
        if other == self.func:
            return self

        handler = {"id": str(other.im_self.getLocation()), "method": other.__name__}

        proxy = getattr(self.instance, EVENTS_PROXY_NAME)
        proxy.subscribe(self.func.__name__, handler)

        return self

    def __isub__(self, other):
        if other == self.func:
            return self

        handler = {"id": str(other.im_self.getLocation()), "method": other.__name__}

        proxy = getattr(self.instance, EVENTS_PROXY_NAME)
        proxy.unsubscribe(self.func.__name__, handler)

        return self
