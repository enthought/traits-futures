# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
asyncio cross-thread pinger.

This module provides a way for a background thread to request that
the main thread execute a (fixed, parameterless) callback.
"""

import asyncio


class Pingee:
    """
    Receiver for pings.

    Parameters
    ----------
    on_ping : callable
        Zero-argument callable that's executed on the main thread as a
        result of each ping.
    """

    def __init__(self, on_ping):
        self._event_loop = asyncio.get_event_loop()
        self._on_ping = on_ping


class Pinger:
    """
    Ping emitter, which can emit pings in a thread-safe manner.

    Parameters
    ----------
    pingee : Pingee
        The corresponding ping receiver.
    """

    def __init__(self, pingee):
        self.pingee = pingee

    def connect(self):
        """
        Connect to the ping receiver. No pings should be sent until
        this function is called.
        """
        pass

    def disconnect(self):
        """
        Disconnect from the ping receiver. No pings should be sent
        after calling this function.
        """
        pass

    def ping(self):
        """
        Send a ping to the receiver.
        """
        event_loop = self.pingee._event_loop
        event_loop.call_soon_threadsafe(self.pingee._on_ping)
