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
wxPython cross-thread pinger.

This module provides a way for a background thread to request that
the main thread execute a (fixed, parameterless) callback.
"""

import wx.lib.newevent


#: Create new event type that's unique to the Pinger infrastructure.
_PingEvent, _PingEventBinder = wx.lib.newevent.NewEvent()


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
        Send a ping to the ping receiver.
        """
        wx.PostEvent(self.pingee, _PingEvent())


class Pingee(wx.EvtHandler):
    """
    Receiver for pings.

    Parameters
    ----------
    on_ping : callable
        Zero-argument callable that's called on the main thread
        every time a ping is received.
    """

    def __init__(self, on_ping):
        wx.EvtHandler.__init__(self)
        self._on_ping = on_ping
        self.Bind(_PingEventBinder, self._on_ping_event)

    def _on_ping_event(self, event):
        """
        Handler for events of type _PING_EVENT_TYPE.
        """
        self._on_ping()
