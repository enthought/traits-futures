# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

import threading
import unittest

from traits.api import Event, HasStrictTraits, Instance, Int

from traits_futures.toolkit_support import toolkit

GuiTestAssistant = toolkit("gui_test_assistant:GuiTestAssistant")
Pingee = toolkit("pinger:Pingee")
Pinger = toolkit("pinger:Pinger")


class PingerThread(threading.Thread):
    """
    Subclass of thread that sends pings to a target.

    Parameters
    ----------
    pingee : Pingee
        Receiver for the pings.
    ping_count : int, optional
        Number of pings to send (default is 1).

    """

    def __init__(self, pingee, ping_count=1):
        super(PingerThread, self).__init__()
        self.pingee = pingee
        self.ping_count = ping_count

    def run(self):
        pinger = Pinger(self.pingee)
        pinger.connect()
        try:
            for _ in range(self.ping_count):
                pinger.ping()
        finally:
            pinger.disconnect()


class PingListener(HasStrictTraits):
    """
    Listener providing an observable callback for the pingee.
    """

    #: The actual pingee as provided by Traits Futures.
    pingee = Instance(Pingee)

    #: Event fired every time a ping is received.
    ping = Event()

    #: Total number of pings received.
    ping_count = Int(0)

    def _ping_fired(self):
        self.ping_count += 1

    def _pingee_default(self):
        return Pingee(
            on_ping=lambda: setattr(self, "ping", True),
        )


class TestPinger(GuiTestAssistant, unittest.TestCase):
    def setUp(self):
        GuiTestAssistant.setUp(self)
        self.listener = PingListener()

    def tearDown(self):
        del self.listener
        GuiTestAssistant.tearDown(self)

    def test_single_background_ping(self):

        self.assertEqual(self.listener.ping_count, 0)

        t = PingerThread(self.listener.pingee)
        t.start()
        try:
            self.run_until(
                self.listener,
                "ping_count",
                lambda listener: listener.ping_count >= 1,
            )
        finally:
            t.join()

        self.assertEqual(self.listener.ping_count, 1)

    def test_multiple_background_pings(self):
        self.assertEqual(self.listener.ping_count, 0)

        t = PingerThread(self.listener.pingee, ping_count=3)
        t.start()
        try:
            self.run_until(
                self.listener,
                "ping_count",
                lambda listener: listener.ping_count >= 3,
            )
        finally:
            t.join()

        self.assertEqual(self.listener.ping_count, 3)

    def test_multiple_background_pingers(self):
        self.assertEqual(self.listener.ping_count, 0)

        pingers = [
            PingerThread(self.listener.pingee, ping_count=3) for _ in range(5)
        ]

        self.assertEqual(self.listener.ping_count, 0)

        for pinger in pingers:
            pinger.start()
        try:
            self.run_until(
                self.listener,
                "ping_count",
                lambda listener: listener.ping_count >= 15,
            )
        finally:
            for pinger in pingers:
                pinger.join()

        self.assertEqual(self.listener.ping_count, 15)
