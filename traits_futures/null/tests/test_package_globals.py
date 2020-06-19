# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Tests for the null toolkit EventLoop
"""
import unittest

from traits_futures.null.event_loop import EventLoop
from traits_futures.null.package_globals import get_event_loop, set_event_loop


class TestEventLoop(unittest.TestCase):
    def test_get_and_set_event_loop(self):
        event_loop = EventLoop()
        old_event_loop = get_event_loop()
        self.assertNotEqual(old_event_loop, event_loop)
        set_event_loop(event_loop)
        try:
            self.assertEqual(get_event_loop(), event_loop)
        finally:
            set_event_loop(old_event_loop)

        self.assertEqual(get_event_loop(), old_event_loop)
