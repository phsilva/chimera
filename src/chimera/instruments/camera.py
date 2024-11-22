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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
from math import pi, cos, sin

import threading
import time
import os
import datetime as dt

from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.camera import (CameraExpose, CameraTemperature,
                                       CameraInformation,
                                       InvalidReadoutMode, Shutter)
from chimera.controllers.imageserver.imagerequest import ImageRequest
from chimera.controllers.imageserver.util import getImageServer
from chimera.core.lock import lock
from chimera.util.image import Image, ImageUtil


class CameraBase (ChimeraObject,
                  CameraExpose, CameraTemperature, CameraInformation):

    def __init__(self):
        ChimeraObject.__init__(self)

        self.abort = threading.Event()
        self.abort.clear()

        self.__isExposing = threading.Event()

        self.extra_header_info = dict()

    def __stop__(self):
        self.abortExposure(readout=False)

    def get_extra_header_info(self):
        return self.extra_header_info

    @lock
    def expose(self, request=None, **kwargs):

        self.__isExposing.set()

        try:
            return self._baseExpose(request, **kwargs)
        finally:
            self.__isExposing.clear()

    def _baseExpose(self, request, **kwargs):

        if request:

            if isinstance(request, ImageRequest):
                imageRequest = request
            elif isinstance(request, dict):
                imageRequest = ImageRequest(**request)
        else:
            if kwargs:
                imageRequest = ImageRequest(**kwargs)
            else:
                imageRequest = ImageRequest()

        frames = imageRequest['frames']
        interval = imageRequest['interval']

        # validate shutter
        if str(imageRequest["shutter"]).lower() == "open":
            imageRequest["shutter"] = Shutter.OPEN
        elif str(imageRequest["shutter"]).lower() == "close":
            imageRequest["shutter"] = Shutter.CLOSE
        else:
            imageRequest["shutter"] = Shutter.LEAVE_AS_IS

        # validate readout mode
        self._getReadoutModeInfo(imageRequest["binning"],
                                 imageRequest["window"])

        # use image server if any and save image on server's default dir if
        # filename given as a relative path.
        server = getImageServer(self.getManager())
        if not os.path.isabs(imageRequest["filename"]):
            imageRequest["filename"] = os.path.join(
                server.defaultNightDir(), imageRequest["filename"])

        # clear abort setting
        self.abort.clear()

        images = []
        manager = self.getManager()

        for frame_num in range(frames):

            # [ABORT POINT]
            if self.abort.is_set():
                return tuple(images)

            imageRequest.beginExposure(manager)
            self._expose(imageRequest)

            # [ABORT POINT]
            if self.abort.is_set():
                return tuple(images)

            image = self._readout(imageRequest)
            if image is not None:
                images.append(image)
                imageRequest.endExposure(manager)

            # [ABORT POINT]
            if self.abort.is_set():
                return tuple(images)

            if (interval > 0 and frame_num < frames) and (not frames == 1):
                time.sleep(interval)

        return tuple(images)

    def abortExposure(self, readout=True):

        if not self.isExposing():
            return False

        # set our event, so current exposure know that it must abort
        self.abort.set()

        # then wait
        while self.isExposing():
            time.sleep(0.1)

        return True

    def _saveImage(self, imageRequest, imageData, extras=None):

        if extras is not None:
            self.extra_header_info = extras

        imageRequest.headers += self.getMetadata(imageRequest)
        img = Image.create(imageData, imageRequest)

        # register image on ImageServer
        server = getImageServer(self.getManager())
        proxy = server.register(img)

        # and finally compress the image if asked
        if imageRequest['compress_format'].lower() != 'no':
            img.compress(format=imageRequest['compress_format'], multiprocess=True)

        return proxy

    def _getReadoutModeInfo(self, binning, window):
        """
        Check if the given binning and window could be used on the given CCD.

        Returns a tuple (modeId, binning, top, left, width, height)
        """

        mode = None

        try:
            binId = self.getBinnings()[binning]
            mode = self.getReadoutModes()[self.getCurrentCCD()][binId]
        except KeyError:
            # use full frame if None given
            binId = self.getBinnings()["1x1"]
            mode = self.getReadoutModes()[self.getCurrentCCD()][binId]

        left = 0
        top = 0
        width, height = mode.getSize()

        if window is not None:
            try:
                xx, yy = window.split(",")
                xx = xx.strip()
                yy = yy.strip()
                x1, x2 = xx.split(":")
                y1, y2 = yy.split(":")

                x1 = int(x1)
                x2 = int(x2)
                y1 = int(y1)
                y2 = int(y2)

                left = min(x1, x2) - 1
                top = min(y1, y2) - 1
                width = (max(x1, x2) - min(x1, x2)) + 1
                height = (max(y1, y2) - min(y1, y2)) + 1

                if left < 0 or left >= mode.width:
                    raise InvalidReadoutMode(
                        "Invalid subframe: left=%d, ccd width (in this binning)=%d" % (left, mode.width))

                if top < 0 or top >= mode.height:
                    raise InvalidReadoutMode(
                        "Invalid subframe: top=%d, ccd height (in this binning)=%d" % (top, mode.height))

                if width > mode.width:
                    raise InvalidReadoutMode(
                        "Invalid subframe: width=%d, ccd width (int this binning)=%d" % (width, mode.width))

                if height > mode.height:
                    raise InvalidReadoutMode(
                        "Invalid subframe: height=%d, ccd height (int this binning)=%d" % (height, mode.height))

            except ValueError:
                left = 0
                top = 0
                width, height = mode.getSize()

        if not binning:
            binning = list(self.getBinnings().keys()).pop(
                list(self.getBinnings().keys()).index("1x1"))

        return mode, binning, top, left, width, height

    def isExposing(self):
        return self.__isExposing.isSet()

    @lock
    def startCooling(self, tempC):
        raise NotImplementedError()

    @lock
    def stopCooling(self):
        raise NotImplementedError()

    def isCooling(self):
        raise NotImplementedError()

    @lock
    def getTemperature(self):
        raise NotImplementedError()

    @lock
    def getSetPoint(self):
        raise NotImplementedError()

    @lock
    def startFan(self, rate=None):
        raise NotImplementedError()

    @lock
    def stopFan(self):
        raise NotImplementedError()

    def isFanning(self):
        raise NotImplementedError()

    def getCCDs(self):
        raise NotImplementedError()

    def getCurrentCCD(self):
        raise NotImplementedError()

    def getBinnings(self):
        raise NotImplementedError()

    def getADCs(self):
        raise NotImplementedError()

    def getPhysicalSize(self):
        raise NotImplementedError()

    def getPixelSize(self):
        raise NotImplementedError()

    def getOverscanSize(self, ccd=None):
        raise NotImplementedError()

    def getReadoutModes(self):
        raise NotImplementedError()

    def supports(self, feature=None):
        raise NotImplementedError()

    def getMetadata(self, request):
        # Check first if there is metadata from an metadata override method.
        md = self.getMetadataOverride(request)
        if md is not None:
            return md
        # If not, just go on with the instrument's default metadata.
        md = [("EXPTIME", float(request['exptime']), "exposure time in seconds"),
              ('IMAGETYP', request['type'].strip(), 'Image type'),
              ('SHUTTER', str(request['shutter']), 'Requested shutter state'),
              ('INSTRUME', str(self['camera_model']), 'Name of instrument'),
              ('CCD',    str(self['ccd_model']), 'CCD Model'),
              ('CCD_DIMX', self.getPhysicalSize()[0], 'CCD X Dimension Size'),
              ('CCD_DIMY', self.getPhysicalSize()[1], 'CCD Y Dimension Size'),
              ('CCDPXSZX', self.getPixelSize()[0], 'CCD X Pixel Size [micrometer]'),
              ('CCDPXSZY', self.getPixelSize()[1], 'CCD Y Pixel Size [micrometer]')]

        if request['window'] is not None:
            md += [('DETSEC', request['window'],
                    'Detector coodinates of the image')]

        if "frame_temperature" in list(self.extra_header_info.keys()):
              md += [('CCD-TEMP', self.extra_header_info["frame_temperature"],
                      'CCD Temperature at Exposure Start [deg. C]')]

        if "frame_start_time" in list(self.extra_header_info.keys()):
            md += [('DATE-OBS', ImageUtil.formatDate(self.extra_header_info.get("frame_start_time")),
                    'Date exposure started')]

        mode, binning, top, left, width, height = self._getReadoutModeInfo(request["binning"], request["window"])
        # Binning keyword: http://iraf.noao.edu/projects/ccdmosaic/imagedef/mosaic/MosaicV1.html
        #    CCD on-chip summing given as two or four integer numbers.  These define
        # the summing of CCD pixels in the amplifier readout order.  The first
        # two numbers give the number of pixels summed in the serial and parallel
        # directions respectively.  If the first pixel read out consists of fewer
        # unbinned pixels along either direction the next two numbers give the
        # number of pixels summed for the first serial and parallel pixels.  From
        # this it is implicit how many pixels are summed for the last pixels
        # given the size of the CCD section (CCDSEC).  It is highly recommended
        # that controllers read out all pixels with the same summing in which
        # case the size of the CCD section will be the summing factors times the
        # size of the data section.
        md += [("CCDSUM", binning.replace("x", " "), "CCD on-chip summing")]

        focal_length = self["telescope_focal_length"]
        if focal_length is not None:  # If there is no telescope_focal_length defined, don't store WCS
            binFactor = self.extra_header_info.get("binning_factor", 1.0)
            pix_w, pix_h = self.getPixelSize()
            focal_length = self["telescope_focal_length"]

            scale_x = binFactor * (((180 / pi) / focal_length) * (pix_w * 0.001))
            scale_y = binFactor * (((180 / pi) / focal_length) * (pix_h * 0.001))

            full_width, full_height = self.getPhysicalSize()
            CRPIX1 = ((int(full_width / 2.0)) - left) - 1
            CRPIX2 = ((int(full_height / 2.0)) - top) - 1

            # Adding WCS coordinates according to FITS standard.
            # Quick sheet: http://www.astro.iag.usp.br/~moser/notes/GAi_FITSimgs.html
            # http://adsabs.harvard.edu/abs/2002A%26A...395.1061G
            # http://adsabs.harvard.edu/abs/2002A%26A...395.1077C
            md += [("CRPIX1", CRPIX1, "coordinate system reference pixel"),
                   ("CRPIX2", CRPIX2, "coordinate system reference pixel"),
                   ("CD1_1",  scale_x * cos(self["rotation"]*pi/180.), "transformation matrix element (1,1)"),
                   ("CD1_2", -scale_y * sin(self["rotation"]*pi/180.), "transformation matrix element (1,2)"),
                   ("CD2_1", scale_x * sin(self["rotation"]*pi/180.), "transformation matrix element (2,1)"),
                   ("CD2_2", scale_y * cos(self["rotation"]*pi/180.), "transformation matrix element (2,2)")]

        return md

