# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Entry point for finding toolkit-specific classes.
"""
# We import QtCore to force an ImportError if Qt is not installed.
from pyface.qt import QtCore  # noqa: F401

from traits_futures.i_gui_context import IGuiContext
from traits_futures.qt.event_loop_helper import EventLoopHelper
from traits_futures.qt.pingee import Pingee


@IGuiContext.register
class QtContext:
    def pingee(self, on_ping):
        """
        Return a new Pingee instance for this toolkit.
        """
        return Pingee(on_ping=on_ping)

    def event_loop_helper(self):
        """
        Return a new EventLoopHelper instance for this toolkit.
        """
        return EventLoopHelper()
