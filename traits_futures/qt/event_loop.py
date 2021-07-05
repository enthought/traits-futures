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
IEventLoop implementation for the Qt event loop.
"""
# We import QtCore to force an ImportError if Qt is not installed.
from pyface.qt import QtCore  # noqa: F401

from traits_futures.i_event_loop import IEventLoop
from traits_futures.qt.event_loop_helper import EventLoopHelper
from traits_futures.qt.pingee import Pingee


@IEventLoop.register
class QtEventLoop:
    """
    IEventLoop implementation for the Qt event loop.
    """

    def pingee(self, on_ping):
        """
        Return a new pingee.

        Parameters
        ----------
        on_ping : callable
            Zero-argument callable, called on the main thread (under a running
            event loop) as a result of each ping sent. The return value of the
            callable is ignored.

        Returns
        -------
        pingee : IPingee
        """
        return Pingee(on_ping=on_ping)

    def event_loop_helper(self):
        """
        Return a new event loop helper.

        Returns
        -------
        event_loop_helper : IEventLoopHelper
        """
        return EventLoopHelper()
