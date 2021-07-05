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
Test mixin for testing IEventLoopHelper implementations.
"""

import contextlib

from traits.api import Bool, Event, HasStrictTraits, Int, on_trait_change

from traits_futures.i_event_loop_helper import IEventLoopHelper


class HasFlag(HasStrictTraits):
    #: Simple true/false flag
    flag = Bool()

    #: Simple event, with no payload
    ping = Event()

    #: Counter for number of pings received.
    ping_count = Int()

    @on_trait_change("ping")
    def increment_ping_count(self):
        self.ping_count += 1


class IEventLoopHelperTests:
    """
    Mixin for testing IEventLoopHelper implementations.

    Unlike other similar event-loop-specific test helpers, this mixin
    should *not* be used alongside the GuiTestAssistant: it's testing
    the foundations that the GuiTestAssistant is built on.
    """

    #: Factory for the event loop. This should be a zero-argument callable
    #: that provides an IEventLoop instance. Must be overridden in subclasses
    #: to run these tests with a particular toolkit.
    event_loop_factory = None

    def setUp(self):
        self._event_loop = self.event_loop_factory()

    def tearDown(self):
        del self._event_loop

    def test_instance_of_i_event_loop_helper(self):
        event_loop_helper = self._event_loop.event_loop_helper()
        self.assertIsInstance(event_loop_helper, IEventLoopHelper)

    def test_run_until_when_condition_becomes_true(self):
        with self.initialised_event_loop_helper() as event_loop:

            # Given
            obj = HasFlag(flag=False)

            # When
            event_loop.setattr_soon(obj, "flag", True)

            # Then
            self.assertFalse(obj.flag)
            event_loop.run_until(
                obj, "flag", lambda obj: obj.flag, timeout=5.0
            )
            self.assertTrue(obj.flag)

    def test_run_until_when_condition_never_true(self):
        with self.initialised_event_loop_helper() as event_loop:

            # Given
            obj = HasFlag(flag=False)

            # Then
            self.assertFalse(obj.flag)
            with self.assertRaises(RuntimeError):
                event_loop.run_until(
                    obj, "flag", lambda obj: obj.flag, timeout=0.1
                )
            self.assertFalse(obj.flag)

    def test_run_until_when_condition_already_true(self):
        with self.initialised_event_loop_helper() as event_loop:

            # Given
            obj = HasFlag(flag=True)

            # Then
            event_loop.run_until(
                obj, "flag", lambda obj: obj.flag, timeout=5.0
            )
            self.assertTrue(obj.flag)

    def test_run_until_with_nontrivial_condition(self):
        with self.initialised_event_loop_helper() as event_loop:

            # Given
            obj = HasFlag(flag=False)

            # When
            event_loop.setattr_soon(obj, "ping", True)
            event_loop.setattr_soon(obj, "ping", True)
            event_loop.setattr_soon(obj, "ping", True)

            # Then
            self.assertFalse(obj.flag)
            event_loop.run_until(
                obj, "ping_count", lambda obj: obj.ping_count >= 3, timeout=5.0
            )
            self.assertEqual(obj.ping_count, 3)

    @contextlib.contextmanager
    def initialised_event_loop_helper(self):
        """
        Context manager that provides an initialised event loop helper.

        The event loop helper is properly shut down on exit of the
        corresponding with block.
        """
        event_loop_helper = self._event_loop.event_loop_helper()
        event_loop_helper.init()
        try:
            yield event_loop_helper
        finally:
            event_loop_helper.dispose()
