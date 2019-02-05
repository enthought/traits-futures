# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Tests for the background iteration functionality.
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import contextlib
import threading
import unittest
import weakref

import six

from traits.api import Any, HasStrictTraits, Instance, List, on_trait_change

from traits_futures.api import (
    IterationFuture, FutureState, TraitsExecutor,
    CANCELLED, CANCELLING, EXECUTING, FAILED, COMPLETED, WAITING,
)
from traits_futures.tests.common_future_tests import CommonFutureTests
from traits_futures.toolkit_support import toolkit

GuiTestAssistant = toolkit("gui_test_assistant:GuiTestAssistant")


#: Timeout for blocking operations, in seconds.
TIMEOUT = 10.0


def reciprocals(start, stop):
    """
    Generate reciprocals of integers in a range.

    Possibly failing iterable used in testing.
    """
    for i in range(start, stop):
        yield 1 / i


def squares(start, stop):
    """
    Generate squares of integers in a range.

    Simple iterable used in testing.
    """
    for i in range(start, stop):
        yield i * i


class IterationFutureListener(HasStrictTraits):
    #: The object we're listening to.
    future = Instance(IterationFuture)

    #: List of states of that future.
    states = List(FutureState)

    #: List of results from the future.
    results = List(Any())

    @on_trait_change("future:state")
    def record_state_change(self, obj, name, old_state, new_state):
        if not self.states:
            # On the first state change, record the initial state as well as
            # the new one.
            self.states.append(old_state)
        self.states.append(new_state)

    @on_trait_change('future:result_event')
    def record_iteration_result(self, result):
        self.results.append(result)


class TestIterationFuture(CommonFutureTests, unittest.TestCase):
    def setUp(self):
        self.future_class = IterationFuture


class TestBackgroundIteration(GuiTestAssistant, unittest.TestCase):
    def setUp(self):
        GuiTestAssistant.setUp(self)
        self.executor = TraitsExecutor()

    def tearDown(self):
        self.halt_executor()
        GuiTestAssistant.tearDown(self)

    def test_successful_iteration(self):
        # A simple case.
        future = self.executor.submit_iteration(reciprocals, start=1, stop=4)
        listener = IterationFutureListener(future=future)

        self.wait_until_done(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [1.0, 0.5, 1 / 3.0])
        self.assertEqual(listener.states, [WAITING, EXECUTING, COMPLETED])

    def test_general_iterable(self):
        # Any call that returns an iterable should be accepted
        future = self.executor.submit_iteration(range, 0, 10, 2)
        listener = IterationFutureListener(future=future)

        self.wait_until_done(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [0, 2, 4, 6, 8])
        self.assertEqual(listener.states, [WAITING, EXECUTING, COMPLETED])

    def test_bad_iteration_setup(self):
        # Deliberately passing a callable that returns
        # something non-iterable.
        future = self.executor.submit_iteration(pow, 2, 5)
        listener = IterationFutureListener(future=future)

        self.wait_until_done(future)

        self.assertException(future, TypeError)
        self.assertEqual(listener.results, [])
        self.assertEqual(listener.states, [WAITING, EXECUTING, FAILED])

    def test_failing_iteration(self):
        # Iteration that eventually fails.
        future = self.executor.submit_iteration(
            reciprocals, start=-2, stop=2)
        listener = IterationFutureListener(future=future)

        self.wait_until_done(future)

        self.assertException(future, ZeroDivisionError)
        self.assertEqual(listener.results, [-0.5, -1.0])
        self.assertEqual(listener.states, [WAITING, EXECUTING, FAILED])

    def test_cancel_before_execution(self):
        # Simulate race condition where we cancel after the background
        # iteration has checked the cancel event, but before we process
        # the STARTED message.
        event = threading.Event()

        def set_then_yield():
            event.set()
            yield 1

        future = self.executor.submit_iteration(set_then_yield)
        listener = IterationFutureListener(future=future)

        self.assertTrue(event.wait(timeout=TIMEOUT))
        self.assertTrue(future.cancellable)
        future.cancel()
        self.wait_until_done(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [])
        self.assertEqual(listener.states, [WAITING, CANCELLING, CANCELLED])

    def test_cancel_during_iteration(self):
        # Exercise code path where the cancel event is set during the
        # iteration.

        blocker = threading.Event()

        def wait_midway():
            yield 1
            blocker.wait(timeout=TIMEOUT)
            yield 2

        future = self.executor.submit_iteration(wait_midway)
        listener = IterationFutureListener(future=future)

        self.run_until(
            listener, "results_items",
            lambda listener: len(listener.results) > 0,
        )

        # task is prevented from completing until we set the blocker event,
        # so we can cancel before that happens.
        self.assertTrue(future.cancellable)
        future.cancel()
        blocker.set()
        self.wait_until_done(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [1])
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancel_before_exhausted(self):
        def yield_then_wait(blocker):
            yield 1
            blocker.wait(timeout=TIMEOUT)

        blocker = threading.Event()
        future = self.executor.submit_iteration(yield_then_wait, blocker)
        listener = IterationFutureListener(future=future)

        # Make sure we've got the single result.
        self.run_until(
            listener, "results_items",
            lambda listener: len(listener.results) > 0,
        )

        self.assertTrue(future.cancellable)
        future.cancel()
        blocker.set()
        self.wait_until_done(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [1])
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancel_before_start(self):
        with self.blocked_thread_pool():
            future = self.executor.submit_iteration(squares, 0, 10)
            listener = IterationFutureListener(future=future)
            self.assertTrue(future.cancellable)
            future.cancel()

        self.wait_until_done(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [])
        self.assertEqual(listener.states, [WAITING, CANCELLING, CANCELLED])

    def test_cancel_after_start(self):
        def target(blocker):
            yield 1729
            blocker.wait(timeout=TIMEOUT)
            yield 2718

        blocker = threading.Event()

        future = self.executor.submit_iteration(target, blocker)
        listener = IterationFutureListener(future=future)

        self.run_until(
            listener, "results_items",
            lambda listener: len(listener.results) > 0,
        )

        self.assertTrue(future.cancellable)
        future.cancel()
        blocker.set()
        self.wait_until_done(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [1729])
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancel_before_failure(self):
        def target(blocker):
            blocker.wait(timeout=TIMEOUT)
            yield 1 / 0

        blocker = threading.Event()

        future = self.executor.submit_iteration(target, blocker)
        listener = IterationFutureListener(future=future)

        self.wait_for_state(future, EXECUTING)
        self.assertTrue(future.cancellable)
        future.cancel()
        blocker.set()
        self.wait_until_done(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [])
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancel_bad_job(self):
        future = self.executor.submit_iteration(pow, 10, 3)
        listener = IterationFutureListener(future=future)

        self.assertTrue(future.cancellable)
        future.cancel()

        self.wait_until_done(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [])
        self.assertEqual(listener.states, [WAITING, CANCELLING, CANCELLED])

    def test_double_cancel(self):
        future = self.executor.submit_iteration(squares, 0, 10)

        self.assertTrue(future.cancellable)
        future.cancel()
        self.assertFalse(future.cancellable)

        with self.assertRaises(RuntimeError):
            future.cancel()

    def test_completed_cancel(self):
        future = self.executor.submit_iteration(squares, 0, 10)

        self.wait_until_done(future)

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

    def test_generator_closed_on_cancellation(self):
        def target(resource_acquired, resource_released, blocker):
            # Generator function that requires cleanup on exit.
            resource_acquired.set()
            try:
                yield 1
                blocker.wait(timeout=TIMEOUT)
                yield 2
            finally:
                resource_released.set()

        resource_acquired = threading.Event()
        blocker = threading.Event()
        resource_released = threading.Event()

        future = self.executor.submit_iteration(
            target,
            resource_acquired, resource_released, blocker)
        listener = IterationFutureListener(future=future)

        self.run_until(
            listener, "results_items",
            lambda listener: len(listener.results) > 0,
        )

        self.assertTrue(resource_acquired.is_set())
        self.assertFalse(resource_released.is_set())

        future.cancel()
        blocker.set()

        self.wait_until_done(future)
        self.assertTrue(resource_released.is_set())

    def test_prompt_result_deletion(self):
        # Check that we're not hanging onto result references needlessly in the
        # background task.
        def waiting_iteration(test_ready, midpoint):
            # Using sets because we need something weakref'able.
            yield {1, 2, 3}
            midpoint.set()
            test_ready.wait(timeout=TIMEOUT)
            yield {4, 5, 6}

        test_ready = threading.Event()
        midpoint = threading.Event()

        future = self.executor.submit_iteration(
            waiting_iteration, test_ready, midpoint)
        listener = IterationFutureListener(future=future)

        self.run_until(
            listener, "results_items",
            lambda listener: len(listener.results) > 0,
        )

        # Check that there are no other references to this result besides
        # the one in this test.
        result = listener.results.pop()
        ref = weakref.ref(result)
        del result

        try:
            # midpoint won't be set until we next invoke "next(iterable)",
            # by which time the IterationBackgroundTask's reference should
            # have been deleted.
            self.assertTrue(midpoint.wait(timeout=TIMEOUT))
            self.assertIsNone(ref())
        finally:
            # Let the background task complete, even if the test fails.
            test_ready.set()

    # Helpers

    @contextlib.contextmanager
    def blocked_thread_pool(self):
        """
        Context manager to temporarily block the threads in the thread pool.
        """
        thread_pool = self.executor._thread_pool
        max_workers = thread_pool._max_workers

        event = threading.Event()

        for _ in range(max_workers):
            thread_pool.submit(event.wait)
        try:
            yield
        finally:
            event.set()

    def halt_executor(self):
        """
        Wait for the executor to stop.
        """
        executor = self.executor
        executor.stop()
        self.run_until(executor, "stopped", lambda executor: executor.stopped)
        del self.executor

    def wait_until_done(self, future):
        self.run_until(future, "done", lambda future: future.done)

    def wait_for_state(self, future, state):
        self.run_until(future, "state", lambda future: future.state == state)

    # Assertions

    def assertException(self, future, exc_type):
        self.assertEqual(future.exception[0], six.text_type(exc_type))

    def assertNoException(self, future):
        with self.assertRaises(AttributeError):
            future.exception
