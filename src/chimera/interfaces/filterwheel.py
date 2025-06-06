# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.interface import Interface
from chimera.core.event import event

from chimera.core.exceptions import ChimeraException


class InvalidFilterPositionException(ChimeraException):
    pass


class FilterWheel(Interface):
    """
    An interface for electromechanical filter wheels.
    Allow simple control and monitor filter changes
    """

    __config__ = {
        "device": "/dev/ttyS0",
        "filter_wheel_model": "Fake Filters Inc.",
        "filters": "R G B LUNAR CLEAR",  # space separated filter names (in position order)
    }

    def set_filter(self, filter):
        """
        Set the current filter.

        @param filter: The filter to use.
        @type  filter: str

        @rtype: None
        """

    def get_filter(self):
        """
        Return the current filter.

        @return: Current filter.
        @rtype: str
        """

    def get_filters(self):
        """
        Return a tuple with the available filter on this wheel.

        @return: Tuple of all filters available.
        @rtype: tuple
        """

    @event
    def filter_change(self, new_filter, old_filter):
        """
        Fired when the wheel changes the current filter.

        @param new_filter: The new current filter.
        @type  new_filter: str

        @param old_filter: The last filter.
        @type  old_filter: str
        """
