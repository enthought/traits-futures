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
    ping = Signal()


class Pinger:
    """
    QObject used to tell the UI that a message is queued.

    This class must be instantiated in the worker thread.
    """

    def __init__(self, signallee):
        self.signaller = _Signaller()
        self.signallee = signallee

    def connect(self):
        """
        Connect to the receiver.
        """
        self.signaller.ping.connect(self.signallee.message_sent)

    def ping(self):
        """
        Send a ping to the receiver.
        """
        self.signaller.ping.emit()

    def disconnect(self):
        """
        Disconnect fom the receiver.
        """
        self.signaller.ping.disconnect(self.signallee.message_sent)
        self.signallee = None


class Pingee(QObject):
    """
    QObject providing a slot for the "message_sent" signal to connect to.

    This object stays in the main thread.
    """

    def __init__(self, on_message_sent):
        QObject.__init__(self)
        self.on_message_sent = on_message_sent

    @Slot()
    def message_sent(self):
        self.on_message_sent()
