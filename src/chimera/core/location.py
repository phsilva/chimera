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

import urlparse
import types
import string

from chimera.core.exceptions import InvalidLocationException


class Location(object):
    """
    Location represents an specific resource available on the system.
    Location is the resource address on the system.

    Location objects are immutable, so please, respect this or hash operations
    will fail.
    """

    host = None
    port = None
    cls  = ""
    name = ""

    def __init__(self, location = None, host = None, port=None, cls=None, name=None):
        # simple string
        if isinstance(location, types.StringType):
            parse_result = urlparse.urlparse(location)
            self.host = parse_result.hostname
            self.port = parse_result.port

            clsname = parse_result.path.strip().split("/")
            if len(clsname) == 3:
                _, self.cls, self.name = clsname

        # copy constructor
        elif isinstance(location, Location):
            self.host = location.host
            self.port = location.port
            self.cls  = location.cls
            self.name = location.name

        # from dict
        else:
            self.host = host
            self.port = port
            self.cls = cls
            self.name = name

        if not self.cls or not self.name:
            raise InvalidLocationException("Location must have class and name.")

        if self.port is not None and type(self.port) != types.IntType:
            raise InvalidLocationException("Location port must be an integer.")

    def __eq__(self, loc):
        if not isinstance(loc, Location):
            loc = Location(loc)

        return (loc.cls.lower() == self.cls.lower()) and (loc.name == self.name)

    def __ne__ (self, loc):
        return not self.__eq__ (loc)

    def __hash__ (self):
        return hash(self.cls) ^ hash(self.name)

    def __repr__(self):
        _str = "/%s/%s" % (self.cls, self.name)

        if self.host and self.port:
            _str = '%s:%d%s' % (self.host, self.port, _str)

        if self.host and not self.port:
            _str = '%s%s' % (self.host, _str)

        return _str
