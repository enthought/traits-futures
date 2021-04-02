# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
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

from traits.api import (
    Event,
    HasStrictTraits,
    Instance,
    Int,
    List,
    on_trait_change,
)

from traits_futures.i_pingee import IPingee
from traits_futures.testing.gui_test_assistant import GuiTestAssistant
from traits_futures.toolkit_support import toolkit

#: Safety timeout, in seconds, for blocking operations, to prevent
#: the test suite from blocking indefinitely if something goes wrong.
SAFETY_TIMEOUT = 10.0


class BackgroundPinger:
    """
    Object allowing pings to be sent from a background thread to a given
    ping receiver.
    """

    def __init__(self, pingee):
        self.pingee = pingee

    def __enter__(self):
        self.ping_request_queue = queue.Queue()
        self.pinger_thread = threading.Thread(target=self._background_task)
        self.pinger_thread.start()
        return self

    def __exit__(self, *exc_info):
        self.ping_request_queue.put(None)
        self.pinger_thread.join(timeout=SAFETY_TIMEOUT)

    def ping(self, ping_count=1):
        """
        Method called from the main thread to request the background
        thread to send the given number of pings.

        Parameters
        ----------
        ping_count : int, optional
            Number of pings to send. Defaults to 1.
        """
        self.ping_request_queue.put(ping_count)

    def _background_task(self):
        """
        Code to be executed on the background thread.

        Waits for ping requests on the ping_request_queue, and then sends
        the appropriate number of pings to the pingee. Exits when the
        value ``None`` is placed on the request queue.
        """
        request_queue = self.ping_request_queue

        pinger = self.pingee.pinger()
        pinger.connect()
        try:
            while True:
                # Timeout should only occur when something's gone wrong.
                ping_count = request_queue.get(timeout=SAFETY_TIMEOUT)
                if ping_count is None:
                    break
                for _ in range(ping_count):
                    pinger.ping()
        finally:
            pinger.disconnect()


class PingListener(HasStrictTraits):
    """
    Listener providing an observable callback for the pingee.
    """

    #: The actual pingee as provided by Traits Futures.
    pingee = Instance(IPingee)

    #: Event fired every time a ping is received.
    ping = Event()

    #: Total number of pings received.
    ping_count = Int(0)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc_info):
        self.disconnect()

    def connect(self):
        self.pingee = toolkit.pingee(
            on_ping=lambda: setattr(self, "ping", True)
        )
        self.pingee.connect()

    def disconnect(self):
        self.pingee.disconnect()
        self.pingee = None

    def _ping_fired(self):
        self.ping_count += 1


class MultipleListeners(HasStrictTraits):
    """
    Listener for PingListeners, accumulating pings from all listeners.
    """

    # The individual PingListeners to listen to.
    listeners = List(Instance(PingListener))

    #: Event fired every time a ping is received.
    ping = Event()

    #: Total number of pings received from all listeners.
    ping_count = Int(0)

    def _ping_fired(self):
        self.ping_count += 1

    @on_trait_change("listeners:ping")
    def _transmit_ping(self):
        self.ping = True


class TestPinger(GuiTestAssistant, unittest.TestCase):
    def setUp(self):
        GuiTestAssistant.setUp(self)
        self.listener = PingListener()
        self.listener.connect()

    def tearDown(self):
        self.listener.disconnect()
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

        self.assertEqual(self.listener.ping_count, 15)

    def test_multiple_pingees(self):
        with PingListener() as listener1:
            with PingListener() as listener2:
                listeners = MultipleListeners(listeners=[listener1, listener2])
                with BackgroundPinger(listener1.pingee) as pinger1:
                    with BackgroundPinger(listener2.pingee) as pinger2:
                        pinger1.ping(3)
                        pinger2.ping(4)

                self.run_until(
                    listeners, "ping", lambda obj: obj.ping_count >= 7
                )

        self.assertEqual(listener1.ping_count, 3)
        self.assertEqual(listener2.ping_count, 4)

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
        self.assertEqual(self.listener.ping_count, 15)

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
