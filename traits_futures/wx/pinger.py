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
wxPython cross-thread pinger functionality.

This module provides a way for a background thread to request that
the main thread execute a (fixed, parameterless) callback.
"""

import wx


#: Event type that's unique to this message. (It's just an integer.)
_PING_EVENT_TYPE = wx.NewEventType()


class _PingEvent(wx.PyCommandEvent):
    """ wx event used to signal that a message has been sent """

    def __init__(self, event_id):
        wx.PyCommandEvent.__init__(self, _PING_EVENT_TYPE, event_id)


class Pinger:
    """
    Ping emitter, which can emit pings in a thread-safe manner.

    Parameters
    ----------
    signallee : Pingee
        The corresponding ping receiver.
    """

    def __init__(self, signallee):
        self.signallee = signallee

    def connect(self):
        """
        Connect to the ping receiver. No pings should be sent until
        this function is called.
        """
        pass

    def disconnect(self):
        """
        Disconnect from the ping receier. No pings should be sent
        after calling this function.
        """
        pass

    def ping(self):
        """
        Send a ping to the ping receiver.
        """
        event = _PingEvent(-1)
        wx.PostEvent(self.signallee, event)


class Pingee(wx.EvtHandler):
    """
    Receiver for pings.

    Parameters
    ----------
    on_message_sent : callable
        Zero-argument callable that's called on the main thread
        every time a ping is received.
    """

    def __init__(self, on_message_sent):
        wx.EvtHandler.__init__(self)
        self._on_ping = on_message_sent
        self._binder = wx.PyEventBinder(_PING_EVENT_TYPE, 1)
        self.Bind(self._binder, self._on_ping_event)

    def _on_ping_event(self, event):
        """
        Handler for events of type _PING_EVENT_TYPE.
        """
        self._on_ping()
