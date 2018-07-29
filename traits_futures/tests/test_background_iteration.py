"""
Tests for the background iteration functionality.
"""
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import concurrent.futures
import contextlib
import threading
import unittest

import six

from traits.api import Any, HasStrictTraits, Instance, List, on_trait_change

from traits_futures.api import (
    IterationFuture, FutureState, TraitsExecutor,
    CANCELLED, CANCELLING, EXECUTING, FAILED, COMPLETED, WAITING,
)
from traits_futures.tests.lazy_message_router import LazyMessageRouter


#: Number of workers for the thread pool.
WORKERS = 4

#: Timeout for queue.get operations, in seconds.
TIMEOUT = 10.0


def reciprocals(start, stop):
    """
    Generate reciprocals of integers in a range.

    Possibly failing iterable used in testing.
    """
    for i in range(start, stop):
        yield 1/i


def squares(start, stop):
    """
    Generate squares of integers in a range.

    Simple iterable used in testing.
    """
    for i in range(start, stop):
        yield i*i


class Listener(HasStrictTraits):
    #: The object we're listening to.
    future = Instance(IterationFuture)

    #: List of states of that future.
    states = List(FutureState)

    #: List of results from the future.
    results = List(Any)

    @on_trait_change("future:state")
    def record_state_change(self, obj, name, old_state, new_state):
        if not self.states:
            # On the first state change, record the initial state as well as
            # the new one.
            self.states.append(old_state)
        self.states.append(new_state)

    @on_trait_change('future:result')
    def record_iteration_result(self, result):
        self.results.append(result)


class TestIterationNoUI(unittest.TestCase):
    """
    Run tests without using any Qt infrastructure.

    We have to explicitly pump the "event loop" to get events.
    """
    def setUp(self):
        self.router = LazyMessageRouter()
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=WORKERS)
        self.executor = TraitsExecutor(
            thread_pool=self.thread_pool,
            _message_router=self.router,
        )

    def tearDown(self):
        self.halt_executor(self.executor)
        self.thread_pool.shutdown()

    def test_successful_iteration(self):
        # A simple case.
        future = self.executor.submit_iteration(reciprocals, start=1, stop=4)
        listener = Listener(future=future)

        self.wait_for_completion(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [1.0, 0.5, 1/3.0])
        self.assertEqual(listener.states, [WAITING, EXECUTING, COMPLETED])

    def test_bad_iteration_setup(self):
        # Deliberately passing a callable that returns
        # something non-iterable.
        future = self.executor.submit_iteration(pow, 2, 5)
        listener = Listener(future=future)

        self.wait_for_completion(future)

        self.assertException(future, TypeError)
        self.assertEqual(listener.results, [])
        self.assertEqual(listener.states, [WAITING, FAILED])

    def test_failing_iteration(self):
        # Iteration that eventually fails.
        future = self.executor.submit_iteration(
            reciprocals, start=-2, stop=2)
        listener = Listener(future=future)

        self.wait_for_completion(future)

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
            yield 2

        future = self.executor.submit_iteration(set_then_yield)
        listener = Listener(future=future)

        event.wait()
        self.assertTrue(future.cancellable)
        future.cancel()
        self.wait_for_completion(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [])
        self.assertEqual(listener.states, [WAITING, CANCELLING, CANCELLED])

    def test_cancel_during_iteration(self):
        # Exercise code path where the cancel event is set during the
        # iteration.

        blocker = threading.Event()

        def wait_midway():
            yield 1
            blocker.wait()
            yield 2

        future = self.executor.submit_iteration(wait_midway)
        listener = Listener(future=future)

        self.router.route_until(
            lambda: len(listener.results) > 0,
            timeout=TIMEOUT,
        )
        # task is prevented from completing until we set the blocker event,
        # so we can cancel before that happens.
        self.assertTrue(future.cancellable)
        future.cancel()
        blocker.set()
        self.wait_for_completion(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [1])
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancel_before_start(self):
        with self.blocked_thread_pool():
            future = self.executor.submit_iteration(squares, 0, 10)
            listener = Listener(future=future)
            self.assertTrue(future.cancellable)
            future.cancel()

        self.wait_for_completion(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [])
        self.assertEqual(listener.states, [WAITING, CANCELLING, CANCELLED])

    def test_cancel_after_start(self):
        future = self.executor.submit_iteration(squares, 0, 10)
        listener = Listener(future=future)

        self.router.route_until(
            lambda: len(listener.results) > 0,
            timeout=TIMEOUT,
        )
        self.assertTrue(future.cancellable)
        future.cancel()
        self.wait_for_completion(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [0])
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancel_before_failure(self):
        future = self.executor.submit_iteration(
            reciprocals, start=-2, stop=2)
        listener = Listener(future=future)

        self.wait_for_state(future, EXECUTING)
        self.assertTrue(future.cancellable)
        future.cancel()
        self.wait_for_completion(future)

        self.assertNoException(future)
        self.assertEqual(listener.results, [])
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancel_bad_job(self):
        future = self.executor.submit_iteration(pow, 10, 3)
        listener = Listener(future=future)

        self.assertTrue(future.cancellable)
        future.cancel()

        self.wait_for_completion(future)

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

        self.wait_for_completion(future)

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

    def test_completed_normal_completion(self):
        future = self.executor.submit_iteration(squares, 0, 10)

        self.assertFalse(future.done)
        self.wait_for_completion(future)
        self.assertTrue(future.done)

    def test_completed_exception(self):
        future = self.executor.submit_iteration(reciprocals, -5, 5)

        self.assertFalse(future.done)
        self.wait_for_completion(future)
        self.assertTrue(future.done)

    def test_completed_bad_iterable(self):
        future = self.executor.submit_iteration(pow, 2, 3)

        self.assertFalse(future.done)
        self.wait_for_completion(future)
        self.assertTrue(future.done)

    def test_completed_cancelled(self):
        future = self.executor.submit_iteration(squares, 0, 10)

        self.assertFalse(future.done)
        future.cancel()
        self.assertFalse(future.done)
        self.wait_for_completion(future)
        self.assertTrue(future.done)

    # Helper functions

    def wait_for_state(self, future, state):
        self.router.route_until(
            lambda: future.state == state, timeout=TIMEOUT)

    def wait_for_completion(self, future):
        self.router.route_until(lambda: future.done, timeout=TIMEOUT)

    def halt_executor(self, executor):
        """
        Stop the executor if necessary, and wait for it to
        reach stopped state.
        """
        if executor.running:
            executor.stop()
        self.router.route_until(lambda: executor.stopped, timeout=TIMEOUT)

    @contextlib.contextmanager
    def blocked_thread_pool(self):
        """
        Context manager to temporarily block the threads in the thread pool.
        """
        event = threading.Event()
        for _ in range(WORKERS):
            self.thread_pool.submit(event.wait)
        try:
            yield
        finally:
            event.set()

    # Assertions

    def assertException(self, future, exc_type):
        self.assertEqual(future.exception[0], six.text_type(exc_type))

    def assertNoException(self, future):
        with self.assertRaises(AttributeError):
            future.exception
