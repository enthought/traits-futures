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
Test mixin for testing implementations of IPingee and IPinger interfaces.
"""

import contextlib
import queue
import threading
import weakref

from traits.api import Bool, Event, HasStrictTraits, Int

#: Safety timeout, in seconds, for blocking operations, to prevent
#: the test suite from blocking indefinitely if something goes wrong.
SAFETY_TIMEOUT = 5.0


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

    #: Event fired every time a ping is received.
    ping = Event()

    #: Total number of pings received.
    ping_count = Int(0)

    def _ping_fired(self):
        self.ping_count += 1

    def fire_ping(self):
        """
        Fire the ping event. This is a convenience method to be used as the
        target for a Pingee's on_ping callback.
        """
        self.ping = True


class IPingeeTests:
    """
    Mixin class for testing IPingee and IPinger implementations.

    Should be used in combination with the GuiTestAssistant.
    """

    def test_single_background_ping(self):
        listener = PingListener()
        with self.connected_pingee(on_ping=listener.fire_ping) as pingee:
            with BackgroundPinger(pingee) as pinger:
                pinger.ping()
                self.assertEventuallyPinged(listener)

    def test_multiple_background_pings(self):
        listener = PingListener()
        with self.connected_pingee(on_ping=listener.fire_ping) as pingee:
            with BackgroundPinger(pingee) as pinger:
                pinger.ping(3)
                pinger.ping(4)
                self.assertEventuallyPinged(listener, ping_count=7)

    def test_multiple_background_pingers(self):
        listener = PingListener()
        with self.connected_pingee(on_ping=listener.fire_ping) as pingee:
            with contextlib.ExitStack() as stack:
                pingers = [
                    stack.enter_context(BackgroundPinger(pingee))
                    for _ in range(5)
                ]

                for pinger in pingers:
                    pinger.ping(3)

                self.assertEventuallyPinged(listener, ping_count=15)

    def test_multiple_pingees(self):
        listener1 = PingListener()
        listener2 = PingListener()

        with self.connected_pingee(on_ping=listener1.fire_ping) as pingee1:
            with self.connected_pingee(on_ping=listener2.fire_ping) as pingee2:
                with BackgroundPinger(pingee1) as pinger1:
                    with BackgroundPinger(pingee2) as pinger2:
                        pinger1.ping(3)
                        pinger2.ping(4)

                self.assertEventuallyPinged(listener1, ping_count=3)
                self.assertEventuallyPinged(listener2, ping_count=4)

    def test_ping_after_pingee_closed(self):
        def send_delayed_ping(pingee, ready):
            """
            Simulate delayed creation of Pinger.
            """
            ready.wait(timeout=SAFETY_TIMEOUT)
            pinger = pingee.pinger()
            pinger.connect()
            try:
                ready.wait(timeout=SAFETY_TIMEOUT)
                pinger.ping()
            finally:
                pinger.disconnect()

        listener = PingListener()
        with self.connected_pingee(on_ping=listener.fire_ping) as pingee:
            ready = threading.Event()
            pinger_thread = threading.Thread(
                target=send_delayed_ping,
                args=(pingee, ready),
            )
            pinger_thread.start()

        ready.set()

        # There shouldn't be any ping-related activity queued on the event
        # loop at this point. We exercise the event loop, in the hope
        # of flushing out any such activity.

        class Sentinel(HasStrictTraits):
            #: Simple boolean flag.
            flag = Bool(False)

        sentinel = Sentinel()

        self._event_loop_helper.setattr_soon(sentinel, "flag", True)
        self.run_until(sentinel, "flag", lambda sentinel: sentinel.flag)

        self.assertEqual(listener.ping_count, 0)

    def test_disconnect_removes_callback_reference(self):
        # Implementation detail: after disconnection, the pingee should
        # no longer hold a reference to its callback.

        def do_nothing():
            pass

        finalizer = weakref.finalize(do_nothing, lambda: None)

        pingee = self._gui_context.pingee(on_ping=do_nothing)
        pingee.connect()
        del do_nothing

        self.assertTrue(finalizer.alive)
        pingee.disconnect()
        self.assertFalse(finalizer.alive)

    def test_background_threads_finish_before_event_loop_starts(self):
        # Previous tests keep the background threads running until we've
        # received the expected number of pings. But that shouldn't be
        # necessary.
        listener = PingListener()
        with self.connected_pingee(on_ping=listener.fire_ping) as pingee:
            with contextlib.ExitStack() as stack:
                pingers = [
                    stack.enter_context(BackgroundPinger(pingee))
                    for _ in range(5)
                ]

                for pinger in pingers:
                    pinger.ping(3)

            # Delete all resources associated to the pingers.
            del pingers, stack

            # Note: threads have all already completed and exited before we
            # start running the event loop.
            self.assertEventuallyPinged(listener, ping_count=15)

    @contextlib.contextmanager
    def connected_pingee(self, on_ping):
        """
        Context manager providing a connected pingee.

        Disconnects the pingee on with block exit.

        Parameters
        ----------
        on_ping : callable
            Callback to execute whenever a ping is received.
        """
        pingee = self._gui_context.pingee(on_ping=on_ping)
        pingee.connect()
        try:
            yield pingee
        finally:
            pingee.disconnect()

    def assertEventuallyPinged(self, listener, *, ping_count=1):
        """
        Assert that we eventually receive at least some number of pings.

        Runs the event loop until either timeout or the expected number
        of pings is received.

        Parameters
        ----------
        listener : PingListener
            The listener to monitor for pings.
        ping_count : int, optional
            The number of pings that listener expects to receive.
            The default is 1.
        """
        self.run_until(
            listener,
            "ping_count",
            lambda listener: listener.ping_count >= ping_count,
        )
        # Double check that we received _exactly_ the expected number
        # of pings, and no more.
        self.assertEqual(listener.ping_count, ping_count)
