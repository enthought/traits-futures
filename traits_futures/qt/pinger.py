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
Qt cross-thread pinger.

This module provides a way for a background thread to request that
the main thread execute a (fixed, parameterless) callback.
"""

from pyface.qt.QtCore import QObject, Qt, Signal, Slot


class _Signaller(QObject):
    """
    Private object used to send signals to the corresponding Qt receiver.
    """

    ping = Signal()


class Pingee(QObject):
    """
    Receiver for pings.

    Whenever a ping is received from a linked Pingee, the receiver
    calls the given fixed parameterless callable.

    The ping receiver must be connected (using the ``connect``) method
    before use, and should call ``disconnect`` when it's no longer
    expected to receive pings.

    Parameters
    ----------
    on_ping : callable
        Zero-argument callable that's called on the main thread
        every time a ping is received.
    """

    def __init__(self, on_ping):
        QObject.__init__(self)
        self._on_ping = on_ping

    @Slot()
    def _execute_ping_callback(self):
        self._on_ping()

    def connect(self):
        """
        Prepare Pingee to receive pings.
        """
        pass

    def disconnect(self):
        """
        Undo any connections made in the connect method.
        """
        pass


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
        self._pingee = pingee

    def connect(self):
        """
        Connect to the ping receiver. No pings should be sent until
        this function is called.
        """
        self._signaller = _Signaller()
        self._signaller.ping.connect(
            self._pingee._execute_ping_callback,
            Qt.QueuedConnection,
        )

    def disconnect(self):
        """
        Disconnect from the ping receiver. No pings should be sent
        after calling this function.
        """
        self._signaller.ping.disconnect(self._pingee._execute_ping_callback)
        del self._signaller
        del self._pingee

    def ping(self):
        """
        Send a ping to the receiver.
        """
        self._signaller.ping.emit()
