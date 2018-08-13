from __future__ import absolute_import, print_function, unicode_literals

import contextlib
import operator
import threading
import unittest

import six

from traits.api import HasStrictTraits, Instance, List, on_trait_change

from traits_futures.api import (
    CallFuture, FutureState, TraitsExecutor,
    CANCELLED, CANCELLING, EXECUTING, FAILED, COMPLETED, WAITING,
)
from traits_futures.tests.common_future_tests import CommonFutureTests
from traits_futures.toolkit_support import toolkit

GuiTestAssistant = toolkit("gui_test_assistant:GuiTestAssistant")


#: Timeout for blocking operations, in seconds.
TIMEOUT = 10.0


class CallFutureListener(HasStrictTraits):
    #: Future that we're listening to.
    future = Instance(CallFuture)

    #: List of states of that future.
    states = List(FutureState)

    @on_trait_change("future:state")
    def record_state_change(self, obj, name, old_state, new_state):
        if not self.states:
            # On the first state change, record the initial state as well as
            # the new one.
            self.states.append(old_state)
        self.states.append(new_state)


class TestCallFuture(CommonFutureTests, unittest.TestCase):
    def setUp(self):
        self.future_class = CallFuture


class TestBackgroundCall(GuiTestAssistant, unittest.TestCase):
    def setUp(self):
        GuiTestAssistant.setUp(self)
        self.executor = TraitsExecutor()

    def tearDown(self):
        self.halt_executor()
        GuiTestAssistant.tearDown(self)

    def test_successful_call(self):
        future = self.executor.submit_call(pow, 2, 3)
        listener = CallFutureListener(future=future)

        self.wait_until_done(future)

        self.assertResult(future, 8)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, COMPLETED],
        )

    def test_failed_call(self):
        future = self.executor.submit_call(operator.floordiv, 1, 0)
        listener = CallFutureListener(future=future)

        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertException(future, ZeroDivisionError)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, FAILED],
        )

    def test_cancellation_vs_started_race_condition(self):
        # Simulate situation where a STARTED message arrives post-cancellation.
        event = threading.Event()

        future = self.executor.submit_call(event.set)
        listener = CallFutureListener(future=future)

        # Ensure the background task is past the cancel_event.is_set() check.
        self.assertTrue(event.wait(timeout=TIMEOUT))

        # And _now_ cancel before we process any messages.
        self.assertTrue(future.cancellable)
        future.cancel()
        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_execution(self):
        # Case where cancellation occurs before the future even starts
        # executing.
        with self.blocked_thread_pool():
            future = self.executor.submit_call(pow, 2, 3)
            listener = CallFutureListener(future=future)
            self.assertTrue(future.cancellable)
            future.cancel()

        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_success(self):
        def target(signal, test_ready):
            signal.set()
            test_ready.wait(timeout=TIMEOUT)

        signal = threading.Event()
        test_ready = threading.Event()

        future = self.executor.submit_call(target, signal, test_ready)
        listener = CallFutureListener(future=future)

        # Wait for executing state; the test_ready event ensures we
        # get no further.
        self.assertTrue(signal.wait(timeout=TIMEOUT))
        self.wait_for_state(future, EXECUTING)

        self.assertTrue(future.cancellable)
        future.cancel()
        test_ready.set()
        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_failure(self):
        def target(signal, test_ready):
            signal.set()
            test_ready.wait(timeout=TIMEOUT)
            1 / 0

        signal = threading.Event()
        test_ready = threading.Event()

        future = self.executor.submit_call(target, signal, test_ready)
        listener = CallFutureListener(future=future)

        # Wait for executing state; the test_ready event ensures we
        # get no further.
        self.assertTrue(signal.wait(timeout=TIMEOUT))
        self.wait_for_state(future, EXECUTING)

        self.assertTrue(future.cancellable)
        future.cancel()
        test_ready.set()
        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cannot_cancel_after_success(self):
        future = self.executor.submit_call(pow, 2, 3)
        listener = CallFutureListener(future=future)

        self.wait_until_done(future)

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

        self.assertResult(future, 8)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, COMPLETED],
        )

    def test_cannot_cancel_after_failure(self):
        future = self.executor.submit_call(operator.floordiv, 1, 0)
        listener = CallFutureListener(future=future)

        self.wait_until_done(future)

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

        self.assertNoResult(future)
        self.assertException(future, ZeroDivisionError)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, FAILED],
        )

    def test_cannot_cancel_after_cancel(self):
        future = self.executor.submit_call(pow, 2, 3)
        listener = CallFutureListener(future=future)

        self.assertTrue(future.cancellable)
        future.cancel()
        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_double_cancel_variant(self):
        def target(signal, test_ready):
            signal.set()
            test_ready.wait(timeout=TIMEOUT)

        signal = threading.Event()
        test_ready = threading.Event()

        future = self.executor.submit_call(target, signal, test_ready)
        listener = CallFutureListener(future=future)

        # Wait for executing state; the test_ready event ensures we
        # get no further.
        self.assertTrue(signal.wait(timeout=TIMEOUT))
        self.wait_for_state(future, EXECUTING)

        self.assertTrue(future.cancellable)
        future.cancel()
        test_ready.set()

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

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

    def assertResult(self, future, expected_result):
        self.assertEqual(future.result, expected_result)

    def assertNoResult(self, future):
        with self.assertRaises(AttributeError):
            future.result

    def assertException(self, future, exc_type):
        self.assertEqual(future.exception[0], six.text_type(exc_type))

    def assertNoException(self, future):
        with self.assertRaises(AttributeError):
            future.exception
