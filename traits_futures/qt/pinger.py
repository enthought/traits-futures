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
Qt cross-thread pinger functionality.

This module provides a way for a background thread to request that
the main thread execute a (fixed, parameterless) callback.
"""

from pyface.qt.QtCore import QObject, Signal, Slot


class _Signaller(QObject):
    """
    Private object used to send signals to the corresponding Qt receiver.
    """

    ping = Signal()


class Pinger:
    """
    Ping emitter, which can emit pings in a thread-safe manner.

    Parameters
    ----------
    pingee : Pingee
        The corresponding ping receiver.
    """

    def __init__(self, pingee):
        self._signaller = _Signaller()
        self._pingee = pingee

    def connect(self):
        """
        Connect to the ping receiver. No pings should be sent until
        this function is called.
        """
        self._signaller.ping.connect(self._pingee.message_sent)

    def ping(self):
        """
        Send a ping to the receiver.
        """
        self._signaller.ping.emit()

    def disconnect(self):
        """
        Disconnect from the ping receiver. No pings should be sent
        after calling this function.
        """
        self._signaller.ping.disconnect(self._pingee.message_sent)
        self._pingee = None


class Pingee(QObject):
    """
    Receiver for pings.

    Parameters
    ----------
    on_ping : callable
        Zero-argument callable that's called on the main thread
        every time a ping is received.
    """

    def __init__(self, on_ping):
        QObject.__init__(self)
        self.on_ping = on_ping

    @Slot()
    def message_sent(self):
        self.on_ping()
