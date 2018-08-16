"""
Tests for the null toolkit EventLoop
"""
from __future__ import absolute_import, print_function, unicode_literals

import unittest

from traits.api import Event, HasStrictTraits, Instance

from traits_futures.null.event_loop import (
    EventLoop,
    clear_event_loop,
    get_event_loop,
    set_event_loop,
)


class EventLoopStopper(HasStrictTraits):
    #: The event loop to stop.
    event_loop = Instance(EventLoop)

    #: The event that will be fired to stop the event loop.
    stop = Event

    def _stop_fired(self):
        self.event_loop.stop()


class TestEventLoop(unittest.TestCase):
    def test_stops_on_stop(self):
        event_loop = EventLoop()
        stopper = EventLoopStopper(event_loop=event_loop)
        poster = event_loop.event_poster(stopper, "stop")
        poster.post_event(True)

        # Event loop should process the posted event and stop.
        stopped = event_loop.start(timeout=10.0)
        self.assertTrue(stopped)

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
        set_event_loop(event_loop)
        self.assertEqual(get_event_loop(), event_loop)

    def test_get_event_loop_no_event_loop(self):
        with self.assertRaises(RuntimeError):
            get_event_loop()

    def test_clear_event_loop(self):
        event_loop = EventLoop()
        set_event_loop(event_loop)
        clear_event_loop()
        with self.assertRaises(RuntimeError):
            get_event_loop()
