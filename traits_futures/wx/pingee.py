# (C) Copyright 2018-2023 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
wxPython cross-thread pinger.

This module provides a way for a background thread to request that
the main thread execute a (fixed, parameterless) callback.
"""

import wx.lib.newevent

from traits_futures.i_pingee import IPingee, IPinger

# Note: we're not using the more obvious spelling
#   _PingEvent, _PingEventBinder = wx.lib.newevent.NewEvent()
# here because that confuses Sphinx's autodoc mocking.
# Ref: enthought/traits-futures#263.

#: New event type that's unique to the Pinger infrastructure.
_PingEventPair = wx.lib.newevent.NewEvent()
_PingEvent = _PingEventPair[0]
_PingEventBinder = _PingEventPair[1]


@IPingee.register
class Pingee(wx.EvtHandler):
    """
    Receiver for pings.

    Whenever a ping is received from a linked Pinger, the receiver
    calls the given fixed parameterless callable.

    The ping receiver must be connected (using the ``connect``) method
    before use, and should call ``disconnect`` when it's no longer
    expected to receive pings.

    Parameters
    ----------
    on_ping
        Zero-argument callable that's called on the main thread
        every time a ping is received.
    """

    def __init__(self, on_ping):
        wx.EvtHandler.__init__(self)
        self._on_ping = lambda event: on_ping()

    def connect(self):
        """
        Prepare Pingee to receive pings.
        """
        self.Bind(_PingEventBinder, handler=self._on_ping)

    def disconnect(self):
        """
        Disconnect from the on_ping callable.
        """
        self.Unbind(_PingEventBinder, handler=self._on_ping)
        del self._on_ping

    def pinger(self):
        """
        Create and return a new pinger linked to this pingee.

        This method is thread-safe. Typically the pingee will be passed to
        a background thread, and this method used within that background thread
        to create a pinger.

        This method should only be called after the 'connect' method has
        been called.

        Returns
        -------
        pinger : Pinger
            New pinger, linked to this pingee.
        """
        return Pinger(pingee=self)


@IPinger.register
class Pinger:
    """
    Ping emitter, which can send pings to a receiver in a thread-safe manner.

    Parameters
    ----------
    pingee : Pingee
        The target receiver for the pings. The receiver must already be
        connected.
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
        del self.pingee

    def ping(self):
        """
        Send a ping to the ping receiver.
        """
        wx.PostEvent(self.pingee, _PingEvent())
