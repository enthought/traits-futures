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
Tests for the TestAssistant.
"""
import time
import unittest.mock

from traits.api import Event, HasStrictTraits

from traits_futures.api import (
    CANCELLED,
    MultithreadingContext,
    submit_call,
    TraitsExecutor,
)
from traits_futures.testing.test_assistant import TestAssistant

#: Maximum timeout for blocking calls, in seconds. A successful test should
#: never hit this timeout - it's there to prevent a failing test from hanging
#: forever and blocking the rest of the test suite.
SAFETY_TIMEOUT = 5.0


class Dummy(HasStrictTraits):
    never_fired = Event()


def slow_return():
    """
    Return after a delay.
    """
    time.sleep(0.1)
    return 1729


class TestTestAssistant(TestAssistant, unittest.TestCase):
    def setUp(self):
        TestAssistant.setUp(self)

    def tearDown(self):
        TestAssistant.tearDown(self)

    def test_run_until_timeout(self):
        # Trait never fired, condition never true.
        dummy = Dummy()

        start_time = time.monotonic()
        with self.assertRaises(RuntimeError):
            self.run_until(
                dummy,
                "never_fired",
                condition=lambda object: False,
                timeout=0.1,
            )
        actual_timeout = time.monotonic() - start_time
        # We're being ultra-conservative here; on a typical system, the actual
        # time taken to fail shouldn't be much more than the 0.1 timeout. But
        # at least this test catches the bug of using the default timeout of 10
        # seconds.
        self.assertLess(actual_timeout, 1.0)

    def test_run_until_timeout_trait_fired(self):
        # Trait fired, but condition still never true.
        executor = TraitsExecutor(
            context=MultithreadingContext(),
            event_loop=self._event_loop,
        )
        future = submit_call(executor, int, "111")
        start_time = time.monotonic()
        with self.assertRaises(RuntimeError):
            self.run_until(
                future,
                "state",
                condition=lambda future: future.state == CANCELLED,
                timeout=0.1,
            )
        actual_timeout = time.monotonic() - start_time

        executor.shutdown(timeout=SAFETY_TIMEOUT)
        self.assertLess(actual_timeout, 1.0)

    def test_run_until_timeout_with_true_condition(self):
        # Trait never fired, but condition true anyway.
        dummy = Dummy()
        start_time = time.monotonic()
        self.run_until(
            dummy,
            "never_fired",
            condition=lambda object: True,
            timeout=10.0,
        )
        actual_timeout = time.monotonic() - start_time
        # The actual time take for the run_until call to return should
        # be close to zero.
        self.assertLess(actual_timeout, 1.0)

    def test_run_until_success(self):
        # Trait fired, condition starts false but becomes true.
        executor = TraitsExecutor(
            context=MultithreadingContext(),
            event_loop=self._event_loop,
        )

        # Case 1: condition true on second trait change event.
        future = submit_call(executor, slow_return)
        self.run_until(
            future,
            "state",
            condition=lambda future: future.done,
        )
        self.assertTrue(future.done)

        # Case 2: condition true on the first trait firing.
        executor.stop()
        self.run_until(
            executor,
            "stopped",
            condition=lambda executor: executor.stopped,
        )
        self.assertTrue(executor.stopped)

    def test_exercise_event_loop(self):
        # There's little that we can usefully test here: exercising the event
        # loop is *likely* to flush out pending events, but there are no
        # *guaranteed* observable changes from exercising the event loop. So we
        # merely call the method to check that it exists, and check that
        # the event loop helper's run_until was called as a side-effect.
        with unittest.mock.patch.object(
            self._event_loop_helper,
            "run_until",
            wraps=self._event_loop_helper.run_until,
        ) as mock_run_until:
            self.exercise_event_loop()
        mock_run_until.assert_called()
