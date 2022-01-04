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
IEventLoop implementation wrapping an asyncio event loop.
"""
import asyncio
import warnings

from traits_futures.asyncio.event_loop_helper import EventLoopHelper
from traits_futures.asyncio.pingee import Pingee
from traits_futures.i_event_loop import IEventLoop


@IEventLoop.register
class AsyncioEventLoop:
    """
    IEventLoop implementation wrapping an asyncio event loop.

    Parameters
    ----------
    event_loop : asyncio.AbstractEventLoop, optional
        The asyncio event loop to wrap. If not provided, a new
        event loop will be created and used.
    """

    def __init__(self, *, event_loop=None):
        own_event_loop = event_loop is None
        if own_event_loop:
            warnings.warn(
                (
                    "The event_loop parameter to AsyncioEventLoop will "
                    "become required in a future version of Traits Futures"
                ),
                DeprecationWarning,
            )
            event_loop = asyncio.new_event_loop()

        self._own_event_loop = own_event_loop
        self._event_loop = event_loop

    def close(self):
        """
        Free any resources allocated by this object.
        """
        if self._own_event_loop:
            self._event_loop.close()

    def pingee(self, on_ping):
        """
        Return a new pingee.

        Parameters
        ----------
        on_ping
            Zero-argument callable, called on the main thread (under a running
            event loop) as a result of each ping sent. The return value of the
            callable is ignored.

        Returns
        -------
        pingee : IPingee
        """
        return Pingee(on_ping=on_ping, event_loop=self._event_loop)

    def helper(self):
        """
        Return a new event loop helper.

        Returns
        -------
        event_loop_helper : IEventLoopHelper
        """
        return EventLoopHelper(event_loop=self._event_loop)
