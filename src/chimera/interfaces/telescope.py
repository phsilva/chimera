# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from chimera.core.interface import Interface
from chimera.core.event import event
from chimera.core.exceptions import ChimeraException
from chimera.util.enum import Enum
from chimera.util.position import Position


class AlignMode(Enum):
    ALT_AZ = "ALT_AZ"
    POLAR = "POLAR"
    LAND = "LAND"


class SlewRate(Enum):
    GUIDE = "GUIDE"
    CENTER = "CENTER"
    FIND = "FIND"
    MAX = "MAX"


class TelescopeStatus(Enum):
    OK = "OK"
    ERROR = "ERROR"
    ABORTED = "ABORTED"
    OBJECT_TOO_LOW = "OBJECT_TOO_LOW"
    OBJECT_TOO_HIGH = "OBJECT_TOO_HIGH"


class TelescopePierSide(Enum):
    EAST = "EAST"
    WEST = "WEST"
    UNKNOWN = "UNKNOWN"


class PositionOutsideLimitsException(ChimeraException):
    pass


class Telescope(Interface):
    """
    Telescope base interface.
    """

    __config__ = {
        "device": None,
        "model": "Fake Telescopes Inc.",
        "optics": ["Newtonian", "SCT", "RCT"],
        "mount": "Mount type Inc.",
        "aperture": 100.0,  # mm
        "focal_length": 1000.0,  # mm unit (ex., 0.5 for a half length focal reducer)
        "focal_reduction": 1.0,
        "fans": [],  # Represents a list of fans of the telescope, i.e.:
        # fans: ['/FakeFan/fake1', '/FakeFan/fake2']
    }


class TelescopeSlew(Telescope):
    """
    Basic interface for telescopes.
    """

    __config__ = {
        "timeout": 30,  # s
        "slew_rate": SlewRate.MAX,
        "auto_align": True,
        "align_mode": AlignMode.POLAR,
        "slew_idle_time": 0.1,  # s
        "max_slew_time": 90.0,  # s
        "stabilization_time": 2.0,  # s
        "position_sigma_delta": 60.0,  # arcseconds
        "skip_init": False,
        "min_altitude": 20,
    }

    def slewToObject(self, name):
        """
        Slew the scope to the coordinates of the given
        object. Object name will be converted to a coordinate using a
        resolver like SIMBAD or NED.

        @param name: Object name to slew to.
        @type  name: str

        @returns: Nothing.
        @rtype: None
        """

    def slewToRaDec(self, position):
        """
        Slew the scope to the given equatorial coordinates.

        @param position: the equatorial coordinates to slew to.
        @type position: L{Position}

        @returns: Nothing.
        @rtype: None
        """

    def slewToAltAz(self, position):
        """
        Slew the scope to the given local coordinates.

        @param position: the local coordinates to slew to.

        @type position: L{Position}

        @returns: Nothing.
        @rtype: None
        """

    def abortSlew(self):
        """
        Try to abort the current slew.

        @return: Nothing.
        @rtype: None
        """

    def isSlewing(self):
        """
        Ask if the telescope is slewing right now.

        @return: True if the telescope is slewing, False otherwise.
        @rtype: bool
        """

    def moveEast(self, offset, rate=SlewRate.MAX):
        """
        Move the scope I{offset} arcseconds East (if offset positive, West
        otherwise)

        @param offset: Arcseconds to move East.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving.
        @type  rate: L{SlewRate}

        @return: Nothing.
        @rtype: None

        @note: float accepted only to make life easier, probably we can't handle such precision.
        """

    def moveWest(self, offset, rate=SlewRate.MAX):
        """
        Move the scope I{offset} arcseconds West (if offset positive, East
        otherwise)

        @param offset: Arcseconds to move West.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving.
        @type  rate: L{SlewRate}

        @return: Nothing.
        @rtype: None

        @note: float accepted only to make life easier, probably we
        can't handle such precision.
        """

    def moveNorth(self, offset, rate=SlewRate.MAX):
        """
        Move the scope I{offset} arcseconds North (if offset positive, South
        otherwise)

        @param offset: Arcseconds to move North.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving.
        @type  rate: L{SlewRate}

        @return: Nothing.
        @rtype: None

        @note: float accepted only to make life easier, probably we
        can't handle such precision.
        """

    def moveSouth(self, offset, rate=SlewRate.MAX):
        """
        Move the scope {offset} arcseconds South (if offset positive, North
        otherwise)

        @param offset: Arcseconds to move South.
        @type  offset: int or float

        @param rate: Slew rate to be used when moving.
        @type  rate: L{SlewRate}

        @return: Nothing.
        @rtype: None

        @note: float accepted only to make life easier, probably we
        can't handle such precision.
        """

    def moveOffset(self, offsetRA, offsetDec, rate=SlewRate.GUIDE):
        """
        @param offsetRA: Arcseconds to move in RA.
        @type  offsetDec: int or float

        @param offsetDec: Arcseconds to move in Dec
        @type  offsetDec: int or float

        @param rate: Slew rate to be used when moving.
        @type  rate: L{SlewRate}

        @return: Nothing.
        @rtype: None

        @note: float accepted only to make life easier, probably we
        can't handle such precision.
        """

    def getRa(self):
        """
        Get the current telescope Right Ascension.

        @return: Telescope's current Right Ascension.
        @rtype: L{Coord}
        """

    def getDec(self):
        """
        Get the current telescope Declination.

        @return: Telescope's current Declination.
        @rtype: L{Coord}
        """

    def getAz(self):
        """
        Get the current telescope Azimuth.

        @return: Telescope's current Azimuth.
        @rtype: L{Coord}
        """

    def getAlt(self):
        """
        Get the current telescope Altitude.

        @return: Telescope's current Alt
        @rtype: L{Coord}
        """

    def getPositionRaDec(self):
        """
        Get the current position of the telescope in equatorial coordinates.

        @return: Telescope's current position (ra, dec).
        @rtype: L{Position}
        """

    def getPositionAltAz(self):
        """
        Get the current position of the telescope in local coordinates.

        @return: Telescope's current position (alt, az).
        @rtype: L{Position}
        """

    def getTargetRaDec(self):
        """
        Get the current telescope target in equatorial coordinates.

        @return: Telescope's current target (ra, dec).
        @rtype: L{Position}
        """

    def getTargetAltAz(self):
        """
        Get the current telescope target in local coordinates.

        @return: Telescope's current target (alt, az).
        @rtype: L{Position}
        """

    @event
    def slewBegin(self, target):
        """
        Indicates that a slew operation started.

        @param target: The target position where the telescope will
        slew to.

        @type target: L{Position}
        """

    @event
    def slewComplete(self, position, status):
        """
        Indicates that the last slew operation finished. This event
        will be fired even when problems impedes complete slew
        (altitude limits, for example). Check L{status} field if you
        need more information.

        @param position: The telescope current position when the slew finished..
        @type  position: L{Position}

        @param status: The status of the slew operation.
        @type  status: L{TelescopeStatus}
        """


class TelescopePier(Telescope):
    def getPierSide(self):
        """
        Get the current side of pier of the telescope.

        @return: Telescope current pier side: UNKNOWN, EAST or WEST.
        @rtype: L{TelescopePierSide}
        """

    def setPierSide(self, side):
        """
        Sets side of pier of the telescope.

        @param side: Side of pier: EAST or WEST
        """


class TelescopeSync(Telescope):
    """
    Telescope with sync support.
    """

    def syncObject(self, name):
        """
        Synchronize the telescope using the coordinates of the
        given object.

        @param name: Object name to sync in.
        @type  name: str
        """

    def syncRaDec(self, position):
        """
        Synchronizes the telescope on the given equatorial
        coordinates.

        This mean different things to different telescopes, but the
        general idea is that after this command, the logical position
        that the telescope will return when asked about will be equal
        to the given position.

        @param position: coordinates to sync on as a Position or a
        tuple with arguments to Position.fromRaDec.

        @type  position: L{Position} or tuple

        @returns: Nothing
        @rtype: None
        """

    @event
    def syncComplete(self, position):
        """
        Fired when a synchronization operation finishes.

        @param position: The position where the telescope synced in.
        @type  position: L{Position}
        """


class TelescopePark(Telescope):
    """
    Telescope with park/unpark support.
    """

    __config__ = {"default_park_position": Position.fromAltAz(90, 180)}

    def park(self):
        """
        Park the telescope on the actual saved park position
        (L{setParkPosition}) or on the default position if none
        set.

        When parked, the telescope will not track objects and may be
        turned off (if the scope was able to).

        @return: Nothing.
        @rtype: None
        """

    def unpark(self):
        """
        Wake up the telescope of the last park operation.

        @return: Nothing.
        @rtype: None
        """

    def isParked(self):
        """
        Ask if the telescope is at park position.

        @return: True if the telescope is parked, False otherwise.
        @rtype: bool
        """

    def setParkPosition(self, position):
        """
        Defines where the scope will park when asked to.

        @param position: local coordinates to park the scope
        @type  position: L{Position}

        @return: Nothing.
        @rtype: None
        """

    def getParkPosition(self):
        """
        Get the Current park position.

        @return: Current park position.
        @rtype: L{Position}
        """

    @event
    def parkComplete(self):
        """
        Indicates that the scope has parked successfully.
        """

    @event
    def unparkComplete(self):
        """
        Indicates that the scope has unparked (waked up)
        successfully.
        """


class TelescopeCover(Telescope):
    """
    Telescope with mirror cover.
    """

    def openCover(self):
        """
        Open the telescope cover

        :return: None
        """

    def closeCover(self):
        """
        Close the telescope cover

        @:return: None
        """

    def isCoverOpen(self):
        """
        Ask if the telescope cover is open or not

        @:return: True if cover is open, false otherwise
        """


class TelescopeTracking(Telescope):
    """
    Telescope with support to start/stop tracking.
    """

    def startTracking(self):
        """
        Start telescope tracking.

        @return: Nothing
        @rtype: None
        """

    def stopTracking(self):
        """
        Stop telescope tracking.

        @return: Nothing
        @rtype: None
        """

    def isTracking(self):
        """
        Ask if the telescope is tracking.

        @return: True if the telescope is tracking, False otherwise.
        @rtype: bool

        """

    @event
    def trackingStarted(self, position):
        """
        Indicates that a tracking operation started.

        @param position: The position where the telescope started track.
        @type  position: L{Position}
        """

    @event
    def trackingStopped(self, position, status):
        """
        Indicates that the last tracking operation stopped. This event
        will be fired even when problems impedes tracking operation to resume
        (altitude limits, for example). Check L{status} field if you
        need more information.

        @param position: The telescope position when tracking stopped.
        @type  position: L{Position}

        @param status: The status of the tracking operation.
        @type  status: L{TelescopeStatus}
        """
