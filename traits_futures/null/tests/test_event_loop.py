"""
Tests for the null toolkit EventLoop
"""
from __future__ import absolute_import, print_function, unicode_literals

import unittest

from traits_futures.null.event_loop import AsyncCaller, EventLoop
from traits_futures.null.package_globals import get_event_loop, set_event_loop

#: The default timeout to use, in seconds.
DEFAULT_TIMEOUT = 10.0


class TestEventLoop(unittest.TestCase):
    def setUp(self):
        # Save the old event loop and create a fresh one for testing.
        self._old_event_loop = get_event_loop()
        self.event_loop = EventLoop()
        set_event_loop(self.event_loop)

    def tearDown(self):
        self.event_loop.run_until_no_handlers(timeout=DEFAULT_TIMEOUT)
        del self.event_loop
        set_event_loop(self._old_event_loop)
        del self._old_event_loop

    def test_stop_immediately(self):
        event_loop = self.event_loop
        stop_event_loop = event_loop.async_caller(event_loop.stop)
        self.assertIsInstance(stop_event_loop, AsyncCaller)

        stop_event_loop()

        # Event loop should process the posted event and stop.
        stopped = event_loop.start(timeout=10.0)
        self.assertTrue(stopped)
        stop_event_loop.close()

    def test_stops_after_timeout(self):
        event_loop = EventLoop()
        stopped = event_loop.start(timeout=0.1)
        self.assertFalse(stopped)

    def test_negative_timeout(self):
        event_loop = EventLoop()
        stopped = event_loop.start(timeout=-10.0)
        self.assertFalse(stopped)

    def test_fire_after_close(self):
        event_loop = self.event_loop
        stop_event_loop = event_loop.async_caller(event_loop.stop)

        stop_event_loop()
        # Safe to close even though events haven't been processed yet.
        stop_event_loop.close()

        stopped = event_loop.start(timeout=10.0)
        self.assertTrue(stopped)

        with self.assertRaises(RuntimeError):
            stop_event_loop()

    def test_run_until_no_handlers(self):
        accumulator = []
        async_append = self.event_loop.async_caller(accumulator.append)
        async_append(4)
        async_append(5)
        async_append.close()

        self.event_loop.run_until_no_handlers(timeout=DEFAULT_TIMEOUT)
        self.assertEqual(accumulator, [4, 5])

    def test_run_until_no_handlers_times_out(self):
        accumulator = []
        async_append = self.event_loop.async_caller(accumulator.append)
        async_append(4)
        async_append(5)

        with self.assertRaises(RuntimeError):
            self.event_loop.run_until_no_handlers(timeout=0.1)

        async_append.close()
