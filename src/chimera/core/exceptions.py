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

import traceback


class ChimeraException(Exception):
    def __init__(self, message, cause=None):
        Exception.__init__(self, message)
        self.cause = cause

    def printStackTrace(self):
        traceback.print_exc()
        if self.cause is not None:
            print '-'*60        
            print "Caused by (remote traceback):"
            print '-'*60        
            print self.cause

class InvalidLocationException(ChimeraException):
    pass

class ObjectNotFoundException(ChimeraException):
    pass

class NotValidChimeraObjectException(ChimeraException):
    pass

class ChimeraObjectException(ChimeraException):
    pass

class ClassLoaderException (ChimeraException):
    pass

class InstrumentBusyException (ChimeraException):
    pass

class OptionConversionException (ChimeraException):
    pass

class ChimeraValueError (ChimeraException):
    pass

class NotImplementedException(ChimeraException):
    pass

class CantPointScopeException(ChimeraException):
    """
    This exception is raised when we cannot center the scope on a field
    It may happen if there is something funny with our fields like:
    faint objects, bright objects, extended objects
    or non-astronomical problems like:
    clouds, mount misalignment, dust cover, etc
    When this happens one can simply go on and observe or ask for a checkPoint
    if checkPoint succeeds then the problem is astronomical
    if checkPoint fails then the problem is non-astronomical
    """


class CanSetScopeButNotThisField(ChimeraException):
    pass

class CantSetScopeException(ChimeraException):
    """
    This exception is raised to indicate we could not set the telescope 
    coordinates when trying to do it on a chosen field.  
    Chosen fields are those known to work for setting the scope.
    So, if it fails we must have some serious problem.
    Might be clouds, might be mount misalignment, dust cover, etc, etc
    Never raise this exception for a science field.  It may be that pointverify 
    fails there because of bright objects or other more astronomical reasons
    """

class NoSolutionAstrometryNetException(ChimeraException):
    """
    This exception is raised to indicate solve-field from astrometry.net could not find
    a solution to the field
    """


class MeadeException(ChimeraException):
    pass

class ProgramExecutionException(ChimeraException):
    pass

class ProgramExecutionAborted(ChimeraException):
    pass

class ObjectTooLowException(ChimeraException):
    pass
