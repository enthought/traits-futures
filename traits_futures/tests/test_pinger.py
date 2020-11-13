# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

import contextlib
import queue
import threading
import unittest

from traits.api import Event, HasStrictTraits, Instance, Int

from traits_futures.toolkit_support import toolkit

GuiTestAssistant = toolkit("gui_test_assistant:GuiTestAssistant")
Pingee = toolkit("pinger:Pingee")
Pinger = toolkit("pinger:Pinger")

#: Safety timeout, in seconds, for blocking operations, to prevent
#: the test suite from blocking indefinitely if something goes wrong.
SAFETY_TIMEOUT = 10.0


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


def ping_sender(pingee, ping_request_queue):
    """
    Pinger task to be executed on a background thread.

    This task receives ping requests on a queue, and pings the given
    pingee the requested number of times.
    """

    pinger = Pinger(pingee)
    pinger.connect()
    try:
        while True:
            # Timeout should only occur when something's gone wrong.
            ping_count = ping_request_queue.get(timeout=SAFETY_TIMEOUT)
            if ping_count is None:
                break
            for _ in range(ping_count):
                pinger.ping()
    finally:
        pinger.disconnect()


class BackgroundPinger:
    """
    Object that sends pings from a background thread.
    """

    def __init__(self, pingee):
        self.pingee = pingee

    def __enter__(self):
        self.ping_request_queue = queue.Queue()
        self.pinger_thread = threading.Thread(
            target=ping_sender,
            args=(self.pingee, self.ping_request_queue),
        )
        self.pinger_thread.start()
        return self

    def __exit__(self, *exc_info):
        self.ping_request_queue.put(None)
        self.pinger_thread.join(timeout=SAFETY_TIMEOUT)

    def ping(self, ping_count=1):
        self.ping_request_queue.put(ping_count)


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

        with BackgroundPinger(self.listener.pingee) as pinger:
            pinger.ping()
            self.assertEventuallyPinged()

        self.assertEqual(self.listener.ping_count, 1)

    def test_multiple_background_pings(self):
        self.assertEqual(self.listener.ping_count, 0)

        with BackgroundPinger(self.listener.pingee) as pinger:
            pinger.ping(3)
            pinger.ping(4)
            self.assertEventuallyPinged(ping_count=7)

        self.assertEqual(self.listener.ping_count, 7)

    def test_multiple_background_pingers(self):
        self.assertEqual(self.listener.ping_count, 0)

        with contextlib.ExitStack() as stack:
            pingers = [
                stack.enter_context(BackgroundPinger(self.listener.pingee))
                for _ in range(5)
            ]

            for pinger in pingers:
                pinger.ping(3)

            self.assertEventuallyPinged(ping_count=15)

    def test_background_threads_finish_before_event_loop_starts(self):
        # Previous tests keep the background threads running until we've
        # received the expected number of pings. But that shouldn't be
        # necessary.
        self.assertEqual(self.listener.ping_count, 0)

        with contextlib.ExitStack() as stack:
            pingers = [
                stack.enter_context(BackgroundPinger(self.listener.pingee))
                for _ in range(5)
            ]

            for pinger in pingers:
                pinger.ping(3)

        # Delete all resources associated to the pingers.
        del pingers, stack

        # Note: threads have all already completed and exited before we start
        # running the event loop.
        self.assertEventuallyPinged(ping_count=15)

    def assertEventuallyPinged(self, ping_count=1):
        """
        Assert that we eventually receive at least some number of pings.

        Runs the event loop until either timeout or the expected number
        of pings is received.

        Parameters
        ----------
        ping_count : int
            The expected number of pings to receive.
        """

        self.run_until(
            self.listener,
            "ping_count",
            lambda listener: listener.ping_count >= ping_count,
        )
