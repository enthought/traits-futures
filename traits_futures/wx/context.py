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
# Force an ImportError if wxPython is not installed.
import wx  # noqa: F401

from traits_futures.i_gui_context import IGuiContext
from traits_futures.wx.event_loop_helper import EventLoopHelper
from traits_futures.wx.pingee import Pingee


@IGuiContext.register
class WxContext:
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
