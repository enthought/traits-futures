"""
Tests for the null toolkit EventLoop
"""
from __future__ import absolute_import, print_function, unicode_literals

import unittest

from traits_futures.null.event_loop import (
    EventLoop,
    get_event_loop,
    set_event_loop,
)


class TestEventLoop(unittest.TestCase):
    def setUp(self):
        # Save the old event loop and create a fresh one for testing.
        self._old_event_loop = get_event_loop()
        self.event_loop = EventLoop()
        set_event_loop(self.event_loop)

    def tearDown(self):
        del self.event_loop
        set_event_loop(self._old_event_loop)
        del self._old_event_loop

    def test_stops_on_stop(self):
        event_loop = self.event_loop

        @event_loop.async_caller
        def stop_event_loop(dummy):
            event_loop.stop()

        stop_event_loop(True)

        # Event loop should process the posted event and stop.
        stopped = event_loop.start(timeout=10.0)
        self.assertTrue(stopped)
        event_loop.disconnect(stop_event_loop)

    def test_stops_after_timeout(self):
        event_loop = EventLoop()
        stopped = event_loop.start(timeout=0.1)
        self.assertFalse(stopped)

    def test_negative_timeout(self):
        event_loop = EventLoop()
        stopped = event_loop.start(timeout=-10.0)
        self.assertFalse(stopped)

    def test_get_event_loop(self):
        event_loop = EventLoop()
        self.assertNotEqual(get_event_loop(), event_loop)
        set_event_loop(event_loop)
        self.assertEqual(get_event_loop(), event_loop)
