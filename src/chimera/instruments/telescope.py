# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.chimeraobject import ChimeraObject

from chimera.interfaces.telescope import (
    TelescopeSlew,
    TelescopeSync,
    TelescopePark,
    TelescopeTracking,
    SlewRate,
)

from chimera.core.lock import lock
from chimera.core.exceptions import ObjectTooLowException

from chimera.util.simbad import Simbad
from chimera.util.position import Epoch, Position


__all__ = ["TelescopeBase"]


class TelescopeBase(
    ChimeraObject, TelescopeSlew, TelescopeSync, TelescopePark, TelescopeTracking
):

    def __init__(self):
        ChimeraObject.__init__(self)

        self._park_position = None
        self.site = None

    @lock
    def slewToObject(self, name):
        target = Simbad.lookup(name)
        self.slewToRaDec(target)

    @lock
    def slewToRaDec(self, position):
        raise NotImplementedError()

    def _validateRaDec(self, position):

        if self.site is None:
            self.site = self.getManager().getProxy("/Site/0")
        lst = self.site.LST()
        latitude = self.site["latitude"]

        altAz = Position.raDecToAltAz(position, latitude, lst)

        return self._validateAltAz(altAz)

    def _validateAltAz(self, position):

        if position.alt <= self["min_altitude"]:
            raise ObjectTooLowException(
                f"Object too close to horizon (alt={position.alt} limit={self['min_altitude']})"
            )

        return True

    def _getFinalPosition(self, position):

        if str(position.epoch).lower() != str(Epoch.NOW).lower():
            self.log.info(
                f"Precessing position ({str(position)}) from {position.epoch} to current epoch."
            )
            position_now = position.precess(Epoch.NOW)
        else:
            self.log.info(f"Current position ({str(position)}), no precession needed.")
            position_now = position

        self.log.info(f"Final precessed position {str(position_now)}")

        return position_now

    @lock
    def slewToAltAz(self, position):
        raise NotImplementedError()

    def abortSlew(self):
        raise NotImplementedError()

    def isSlewing(self):
        raise NotImplementedError()

    @lock
    def moveEast(self, offset, rate=SlewRate.MAX):
        raise NotImplementedError()

    @lock
    def moveWest(self, offset, rate=SlewRate.MAX):
        raise NotImplementedError()

    @lock
    def moveNorth(self, offset, rate=SlewRate.MAX):
        raise NotImplementedError()

    @lock
    def moveSouth(self, offset, rate=SlewRate.MAX):
        raise NotImplementedError()

    @lock
    def moveOffset(self, offsetRA, offsetDec, rate=SlewRate.GUIDE):

        if offsetRA == 0:
            pass
        elif offsetRA > 0:
            self.moveEast(offsetRA, rate)
        else:
            self.moveWest(abs(offsetRA), rate)

        if offsetDec == 0:
            pass
        elif offsetDec > 0:
            self.moveNorth(offsetDec, rate)
        else:
            self.moveSouth(abs(offsetDec), rate)

    def getRa(self):
        raise NotImplementedError()

    def getDec(self):
        raise NotImplementedError()

    def getAz(self):
        raise NotImplementedError()

    def getAlt(self):
        raise NotImplementedError()

    def getPositionRaDec(self):
        raise NotImplementedError()

    def getPositionAltAz(self):
        raise NotImplementedError()

    def getTargetRaDec(self):
        raise NotImplementedError()

    def getTargetAltAz(self):
        raise NotImplementedError()

    @lock
    def syncObject(self, name):
        target = Simbad.lookup(name)
        self.syncRaDec(target)

    @lock
    def syncRaDec(self, position):
        raise NotImplementedError()

    @lock
    def park(self):
        raise NotImplementedError()

    @lock
    def unpark(self):
        raise NotImplementedError()

    def isParked(self):
        raise NotImplementedError()

    @lock
    def setParkPosition(self, position):
        self._park_position = position

    def getParkPosition(self):
        return self._park_position or self["default_park_position"]

    def startTracking(self):
        raise NotImplementedError()

    def stopTracking(self):
        raise NotImplementedError()

    def isTracking(self):
        raise NotImplementedError()

    def getMetadata(self, request):
        # Check first if there is metadata from an metadata override method.
        md = self.getMetadataOverride(request)
        if md is not None:
            return md
        # If not, just go on with the instrument's default metadata.
        position = self.getPositionRaDec()
        alt = self.getAlt()
        return [
            ("TELESCOP", self["model"], "Telescope Model"),
            ("OPTICS", self["optics"], "Telescope Optics Type"),
            ("MOUNT", self["mount"], "Telescope Mount Type"),
            ("APERTURE", self["aperture"], "Telescope aperture size [mm]"),
            ("F_LENGTH", self["focal_length"], "Telescope focal length [mm]"),
            ("F_REDUCT", self["focal_reduction"], "Telescope focal reduction"),
            # TODO: Convert coordinates to proper equinox
            # TODO: How to get ra,dec at start of exposure (not end)
            (
                "RA",
                position.ra.toHMS().__str__(),
                "Right ascension of the observed object",
            ),
            (
                "DEC",
                position.dec.toDMS().__str__(),
                "Declination of the observed object",
            ),
            ("EQUINOX", position.epochString()[1:], "coordinate epoch"),
            ("ALT", alt.toDMS().__str__(), "Altitude of the observed object"),
            ("AZ", self.getAz().toDMS().__str__(), "Azimuth of the observed object"),
            ("AIRMASS", alt.R, "Airmass of the observed object"),
            ("WCSAXES", 2, "wcs dimensionality"),
            ("RADESYS", "ICRS", "frame of reference"),
            ("CRVAL1", position.ra.D, "coordinate system value at reference pixel"),
            ("CRVAL2", position.dec.D, "coordinate system value at reference pixel"),
            ("CTYPE1", "RA---TAN", "name of the coordinate axis"),
            ("CTYPE2", "DEC--TAN", "name of the coordinate axis"),
            ("CUNIT1", "deg", "units of coordinate value"),
            ("CUNIT2", "deg", "units of coordinate value"),
        ]
