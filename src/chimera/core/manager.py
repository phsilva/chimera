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
import threading
import time

from chimera.core.classloader import ClassLoader
from chimera.core.resources   import ResourceManager
from chimera.core.location    import Location
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.proxy         import Proxy
from chimera.core.zygote import Zygote
from chimera.core.exceptions   import InvalidLocationException, \
                                      ObjectNotFoundException, \
                                      NotValidChimeraObjectException, \
                                      ChimeraObjectException

__all__ = ['Manager']


log = logging.getLogger(__name__)

class Manager:

    """
    This is the main class of Chimera.

    Use this class to get Proxies, add objects to the system, and so on.

    This class handles objects life-cycle as described in ILifecycle.

    @group Add/Remove: add*, remove
    @group Start/Stop: start, stop
    @group Shutdown: wait, shutdown
    """

    def __init__(self, host = "localhost", port = 6379):
        log.info("Starting manager.")

        self.resourceManager = ResourceManager(host, port)

        self.zygotes = {}
        self.resources = {}

        self.host = host
        self.port = port

        # shutdown event
        self.died = threading.Event()

    def __repr__ (self):
        return "<Manager for %s:%d at %s>" % (self.host, self.port, hex(id(self)))

    def getHostname (self):
        return self.host

    def getPort (self):
        return self.port

    def shutdown(self):
        """
        Ask the system to shutdown. Closing all sockets and stopping
        all threads.

        @return: Nothing
        @rtype: None
        """

        # die, but only if we are alive ;)
        if not self.died.isSet():

            log.info("Shuting down manager.")

            # stop objects
            try:
                elderly_first = sorted(self.resources.values(),
                                       cmp=lambda x, y: cmp(x.created, y.created),
                                       reverse=True)

                for resource in elderly_first:
                    self.remove(resource.location)
            finally:
                # die!
                self.died.set()
                log.info("Manager finished.")

    def wait (self):
        """
        Ask the system to wait until anyone calls L{shutdown}.

        If nobody calls L{shutdown}, you can stop the system using
        Ctrl+C.

        @return: Nothing
        @rtype: None
        """
        try:
            try:
                while not self.died.isSet():
                    time.sleep(1)
            except IOError:
                # On Windows, Ctrl+C on a sleep call raise IOError 'cause
                # of the interrupted syscall
                pass
        except KeyboardInterrupt:
            # On Windows, Ctrl+C on a sleep call raise IOError 'cause
            # of the interrupted syscall
            self.shutdown()

    def addLocation (self, location, path = None):
        """
        Add the class pointed by 'location' to the system configuring it using 'config'.

        Manager will look for the class in 'path' plus sys.path.

        @param path: The class search path.
        @type path: list

        @raises ChimeraObjectException: Internal error on managed (user) object.
        @raises ClassLoaderException: Class not found.
        @raises NotValidChimeraObjectException: When a object which doesn't inherites from ChimeraObject is given in location.
        @raises InvalidLocationException: When the requested location s invalid.              

        @return: retuns a proxy for the object if sucessuful.
        @rtype: Proxy
        """

        if type(location) != Location:
            location = Location(location)

        # get the class
        class_loader = ClassLoader()
        cls = class_loader.loadClass(location.cls, path)
        return self.addClass(cls, location.name)

    def addClass (self, cls, name):
        """
        Add the class 'cls' to the system configuring it using 'config'.

        @param cls: The class to add to the system.
        @type cls: ChimeraObject

        @param name: The name of the new class instance.
        @type name: str

        @raises ChimeraObjectException: Internal error on managed (user) object.
        @raises NotValidChimeraObjectException: When a object which doesn't inherites from ChimeraObject is given in location.
        @raises InvalidLocationException: When the requested location s invalid.              

        @return: retuns a proxy for the object if sucessuful
        @rtype: Proxy
        """
        location = Location(cls=cls.__name__, name=name)

        # names must not start with a digit
        if location.name[0].isdigit():
            raise InvalidLocationException("Invalid instance name: %s (must start with a letter)" % location)

        if location in self.resources:
            raise InvalidLocationException("Location %s is already in the system. Only one allowed (Tip: change the name!)." % location)

        # check if it's a valid ChimeraObject
        if not issubclass(cls, ChimeraObject):
            raise NotValidChimeraObjectException("Cannot add the class %s. It doesn't descend from ChimeraObject." % cls.__name__)
        
        # start zygote to create the desired object
        resource = self.resourceManager.add(location)

        zygote = Zygote(resource)

        self.resources[location] = resource
        self.zygotes[location] = zygote

        try:
            zygote.start()
            self.start(location)
        except Exception as e:
            self.resourceManager.remove(location)
            del self.zygotes[location]
            del self.resources[location]

            raise e

        return Proxy(location)
       
    def remove (self, location):
        """
        Remove the object pointed by 'location' from the system
        stopping it before if needed.

        @param location: The object to remove.
        @type location: Location,str

        @raises ObjectNotFoundException: When te request object or the Manager was not found.

        @return: retuns True if sucessfull. False otherwise.
        @rtype: bool
        """

        if location not in self.resources:
            raise ObjectNotFoundException ("Location %s was not found." % location)

        self.stop(location)
        self.zygotes[location].stop()

        self.resourceManager.remove(location)

        del self.resources[location]
        del self.zygotes[location]

        return True

    def start (self, location):
        """
        Start the object pointed by 'location'.

        @param location: The object to start.
        @type location: Location or str

        @raises ObjectNotFoundException: When te request object or the Manager was not found.
        @raises ChimeraObjectException: Internal error on managed (user) object.
        
        @return: retuns True if sucessfull. False otherwise.
        @rtype: bool
        """
        return self._lifecycle(location, "__start__", "Starting")

    def stop (self, location):
        """
        Stop the object pointed by 'location'.

        @param location: The object to stop.
        @type location: Location or str

        @raises ObjectNotFoundException: When the requested object or the Manager was not found.
        @raises ChimeraObjectException: Internal error on managed (user) object.

        @return: retuns True if sucessfull. False otherwise.
        @rtype: bool
        """
        return self._lifecycle(location, "__stop__", "Stoping")


    def _lifecycle(self, location, state_method, transition_log):

        if location not in self.resources:
            raise ObjectNotFoundException ("Location %s was not found." % location)
            
        log.info("%s %s." % (transition_log, location))

        try:
            proxy = Proxy(location)
            method = getattr(proxy, state_method)
            method()
        except Exception:
            log.exception("Error running %s %s method." % (state_method, location))
            raise ChimeraObjectException("Error running %s %s method." % (state_method, location))

        return True
