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

from chimera.core.manager    import Manager
from chimera.core.site       import Site
from chimera.core.exceptions import printException

import chimera.core.log

from chimera.util.coord    import Coord
from chimera.util.position import Position

from dateutil.relativedelta import relativedelta

import time
import sys
import logging

class TestSite (object):

    def setup (self):
        self.site = Site()
        self.site += {
            "name": "UFSC",
            "latitude": "-27 36 13 ",
            "longitude": "-48 31 20",
            "altitude": "20"
        }

    def teardown (self):
        self.site = None

    def test_times (self):
        try:
            print
            print "local:", self.site.localtime()
            print "UT   :", self.site.ut()
            print "JD   :", self.site.JD()
            print "MJD  :", self.site.MJD()
            print "LST  :", self.site.LST()
            print "GST  :", self.site.GST()
        except Exception, e:
            printException(e)

    def test_sidereal_clock (self):        
        times = []
        real_times = []
        for i in range (20):
            t0 = time.clock()
            t0_r = time.time()
            print "\r%s" % self.site.LST(),
            times.append(time.clock()-t0)
            real_times.append(time.time()-t0_r)

        print
        print sum(times) / len(times)
        print sum(real_times) / len(real_times)

    def test_astros (self):
        try:
            print
            print "local   :", self.site.localtime()
            print
            print "moonrise  :", self.site.moonrise()
            print "moonset   :", self.site.moonset()
            print "moon pos  :", self.site.moonpos()
            print "moon phase:", self.site.moonphase()
            print
            print "sunrise:", self.site.sunrise()
            print "sunset :", self.site.sunset()
            print "sun pos:", self.site.sunpos()
            print

            sunset_twilight_begin = self.site.sunset_twilight_begin()
            sunset_twilight_end   = self.site.sunset_twilight_end()
            sunset_twilight_duration = relativedelta(sunset_twilight_end, sunset_twilight_begin)
            
            sunrise_twilight_begin = self.site.sunrise_twilight_begin()
            sunrise_twilight_end = self.site.sunrise_twilight_end()
            sunrise_twilight_duration = relativedelta(sunrise_twilight_end, sunrise_twilight_begin)            
            
            print "next sunset twilight begins at:", sunset_twilight_begin
            print "next sunset twilight ends   at:", sunset_twilight_end
            print "sunset twilight duration      :", sunset_twilight_duration
            print
            print "next sunrise twilight begins at:", sunrise_twilight_begin
            print "next sunrise twilight ends   at:", sunrise_twilight_end
            print "sunrise twilight duration      :", sunrise_twilight_duration            

        except Exception, e:
            printException(e)
        
