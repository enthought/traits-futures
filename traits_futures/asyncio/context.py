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
IGuiContext implementation for the main-thread asyncio event loop.
"""
import asyncio

from traits_futures.asyncio.event_loop_helper import EventLoopHelper
from traits_futures.asyncio.pingee import Pingee
from traits_futures.i_gui_context import IGuiContext


@IGuiContext.register
class AsyncioContext:
    """
    IGuiContext implementation for the main-thread asyncio event loop.
    """

    def __init__(self):
        self._event_loop = asyncio.get_event_loop()

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
        return Pingee(on_ping=on_ping, event_loop=self._event_loop)

    def event_loop_helper(self):
        """
        Return a new event loop helper.

        Returns
        -------
        event_loop_helper : IEventLoopHelper
        """
        return EventLoopHelper()
