# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Tests for the background iteration functionality.
"""
import weakref

from traits.api import Any, HasStrictTraits, Instance, List, on_trait_change

from traits_futures.api import (
    CANCELLED,
    CANCELLING,
    COMPLETED,
    EXECUTING,
    FAILED,
    FutureState,
    IterationFuture,
    submit_iteration,
    WAITING,
)

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


def yield_then_wait(barrier):
    """
    Yield a result, then wait for an external event.
    """
    yield 1
    barrier.wait(timeout=TIMEOUT)


def set_then_yield(event):
    """
    Set an event before generating the first result.
    """
    event.set()
    yield 1


def wait_midway(barrier):
    """
    Wait for an external event in the middle of an iteration.
    """
    yield 1729
    barrier.wait(timeout=TIMEOUT)
    yield 2718


def wait_then_fail(barrier):
    """
    Wait for an external event, then fail.
    """
    barrier.wait(timeout=TIMEOUT)
    yield 1 / 0


def ping_pong(test_ready, midpoint):
    """
    Send ping and wait for answering pong mid-iteration.
    """
    # Using sets because we need something weakref'able.
    yield {1, 2, 3}
    midpoint.set()
    test_ready.wait(timeout=TIMEOUT)
    yield {4, 5, 6}


def resource_acquiring_iteration(acquired, released, barrier):
    """
    Iteration that simulates acquiring a resource.
    """
    acquired.set()
    try:
        yield 1
        barrier.wait(timeout=TIMEOUT)
        yield 2
    finally:
        released.set()


def iteration_with_result():
    """
    Iteration that also returns a result.
    """
    yield 1
    yield 2
    return 45


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

    @on_trait_change("future:result_event")
    def record_iteration_result(self, result):
        self.results.append(result)


class BackgroundIterationTests:
    def test_successful_iteration(self):
        # A simple case.
        future = submit_iteration(self.executor, reciprocals, start=1, stop=4)
        listener = IterationFutureListener(future=future)

        self.wait_until_done(future)

        self.assertResult(future, None)
        self.assertNoException(future)
        self.assertEqual(listener.results, [1.0, 0.5, 1 / 3.0])
        self.assertEqual(listener.states, [WAITING, EXECUTING, COMPLETED])

    def test_general_iterable(self):
        # Any call that returns an iterable should be accepted
        future = submit_iteration(self.executor, range, 0, 10, 2)
        listener = IterationFutureListener(future=future)

        self.wait_until_done(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [0, 2, 4, 6, 8])
        self.assertEqual(listener.states, [WAITING, EXECUTING, COMPLETED])

    def test_bad_iteration_setup(self):
        # Deliberately passing a callable that returns
        # something non-iterable.
        future = submit_iteration(self.executor, pow, 2, 5)
        listener = IterationFutureListener(future=future)

        self.wait_until_done(future)

        self.assertException(future, TypeError)
        self.assertEqual(listener.results, [])
        self.assertEqual(listener.states, [WAITING, EXECUTING, FAILED])

    def test_failing_iteration(self):
        # Iteration that eventually fails.
        future = submit_iteration(self.executor, reciprocals, start=-2, stop=2)
        listener = IterationFutureListener(future=future)

        self.wait_until_done(future)

        self.assertException(future, ZeroDivisionError)
        self.assertNoResult(future)
        self.assertEqual(listener.results, [-0.5, -1.0])
        self.assertEqual(listener.states, [WAITING, EXECUTING, FAILED])

    def test_cancel_before_execution(self):
        # Simulate race condition where we cancel after the background
        # iteration has checked the cancel event, but before we process
        # the STARTED message.
        event = self._context.event()

        future = submit_iteration(self.executor, set_then_yield, event)
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

        blocker = self._context.event()

        future = submit_iteration(self.executor, wait_midway, blocker)
        listener = IterationFutureListener(future=future)

        self.run_until(
            listener,
            "results_items",
            lambda listener: len(listener.results) > 0,
        )

        # task is prevented from completing until we set the blocker event,
        # so we can cancel before that happens.
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

    def test_cancel_before_exhausted(self):
        blocker = self._context.event()
        future = submit_iteration(self.executor, yield_then_wait, blocker)
        listener = IterationFutureListener(future=future)

        # Make sure we've got the single result.
        self.run_until(
            listener,
            "results_items",
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
        with self.block_worker_pool():
            future = submit_iteration(self.executor, squares, 0, 10)
            listener = IterationFutureListener(future=future)
            self.assertTrue(future.cancellable)
            future.cancel()

        self.wait_until_done(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [])
        self.assertEqual(listener.states, [WAITING, CANCELLING, CANCELLED])

    def test_cancel_after_start(self):
        blocker = self._context.event()

        future = submit_iteration(self.executor, wait_midway, blocker)
        listener = IterationFutureListener(future=future)

        self.run_until(
            listener,
            "results_items",
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
        blocker = self._context.event()

        future = submit_iteration(self.executor, wait_then_fail, blocker)
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
        future = submit_iteration(self.executor, pow, 10, 3)
        listener = IterationFutureListener(future=future)

        self.assertTrue(future.cancellable)
        future.cancel()

        self.wait_until_done(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [])
        self.assertEqual(listener.states, [WAITING, CANCELLING, CANCELLED])

    def test_double_cancel(self):
        future = submit_iteration(self.executor, squares, 0, 10)

        self.assertTrue(future.cancellable)
        future.cancel()
        self.assertFalse(future.cancellable)

        with self.assertRaises(RuntimeError):
            future.cancel()

    def test_completed_cancel(self):
        future = submit_iteration(self.executor, squares, 0, 10)

        self.wait_until_done(future)

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

    def test_generator_closed_on_cancellation(self):
        resource_acquired = self._context.event()
        blocker = self._context.event()
        resource_released = self._context.event()

        future = submit_iteration(
            self.executor,
            resource_acquiring_iteration,
            resource_acquired,
            resource_released,
            blocker,
        )
        listener = IterationFutureListener(future=future)

        self.run_until(
            listener,
            "results_items",
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
        test_ready = self._context.event()
        midpoint = self._context.event()

        future = submit_iteration(
            self.executor, ping_pong, test_ready, midpoint
        )
        listener = IterationFutureListener(future=future)

        self.run_until(
            listener,
            "results_items",
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

    def test_iteration_with_result(self):
        future = submit_iteration(self.executor, iteration_with_result)
        listener = IterationFutureListener(future=future)

        self.wait_until_done(future)

        self.assertEqual(listener.states, [WAITING, EXECUTING, COMPLETED])
        self.assertEqual(listener.results, [1, 2])
        self.assertResult(future, 45)
        self.assertNoException(future)

    # Helper functions

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

    def assertResult(self, future, expected_result):
        self.assertEqual(future.result, expected_result)

    def assertNoResult(self, future):
        with self.assertRaises(AttributeError):
            future.result

    def assertException(self, future, exc_type):
        self.assertEqual(future.exception[0], str(exc_type))

    def assertNoException(self, future):
        with self.assertRaises(AttributeError):
            future.exception
