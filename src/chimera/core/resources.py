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

import redis as R

from chimera.core.location    import Location
from chimera.core.classloader import ClassLoader
from chimera.core.exceptions  import ObjectNotFoundException
from chimera.core.exceptions  import InvalidLocationException

log = logging.getLogger(__name__)

import sys
import time
import collections
import jsonpickle

class Resource(object):

    def __init__(self, location, bases, created):
        self.location = location
        self.bases = bases
        self.created = created

    def __eq__(self, other):
        return self.location == other.location and self.bases == other.bases


class ResourceManager(object):

    RESOURCES_KEY = "/Chimera/resources"

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.redis = R.StrictRedis(self.host, self.port)

    def add (self, location, loader_path = []):
        location = self._validLocation(location)

        if location in self:
            raise InvalidLocationException("This resource is already registered ('%s')." % str(location))

        bases = []

        classLoader = ClassLoader()

        try:
            cls = classLoader.loadClass(location.cls, path=loader_path)
            bases += map(lambda base: base.__name__, cls.mro())
        except Exception:
            pass

        resource = Resource(location=location, bases=bases, created=time.time())

        self.redis.hset(ResourceManager.RESOURCES_KEY, str(location), jsonpickle.encode(resource))

        return resource

    def remove (self, location):
        return self.redis.hdel(ResourceManager.RESOURCES_KEY, str(location))

    def removeAll(self):
        return self.redis.delete(ResourceManager.RESOURCES_KEY)

    def get (self, location):
        location = self._validLocation(location)
        try:
            index = int(location.name)
            return self._getByIndex(location, index)
        except ValueError:
            # not a numbered instance
            pass

        return self._get(location)

    def getAll(self):
        resources = map(lambda x: jsonpickle.decode(x), self.redis.hvals(ResourceManager.RESOURCES_KEY))
        resources.sort(key=lambda r: r.created)
        return resources

    def getByClass(self, cls):
        resources = filter(lambda resource: cls in resource.bases, self.getAll())
        resources.sort(key=lambda r: r.created)
        return resources

    def _get(self, location):
        location = self._validLocation(location)

        resources = self.getByClass(location.cls)
        locations = [x.location for x in resources]
        
        if location in locations:
            ret = filter(lambda r: r.location == location, resources)
            return ret[0]
        else:
            raise ObjectNotFoundException("Couldn't find %s." % location)


    def _getByIndex(self, location, index):
        location = self._validLocation (location)

        insts = self.getByClass(location.cls)

        if insts:
            try:
                return jsonpickle.decode(self.redis.hget(ResourceManager.RESOURCES_KEY, insts[index].location))
            except IndexError:
                raise ObjectNotFoundException("Couldn't find %s instance #%d." % (location, index))
        else:
            raise ObjectNotFoundException("Couldn't find %s." % location)


    def _validLocation(self, item):
        ret = item

        if not isinstance (item, Location):
            ret = Location (item)

        return ret

    def __getitem__(self, location):
        try:
            return self.get(location)
        except BaseException:
            raise KeyError("Couldn't find %s" % location), None, sys.exc_info()[2]

    def __contains__ (self, location):
        # note that our 'in'/'not in' tests are for keys (locations) and
        # not for values
        try:
            _ = self.get(location)
            return True
        except ObjectNotFoundException:
            return False

    def __len__(self):
        return self.redis.hlen(ResourceManager.RESOURCES_KEY)
