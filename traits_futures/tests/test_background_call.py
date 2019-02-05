# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

from __future__ import absolute_import, print_function, unicode_literals

import concurrent.futures
import contextlib
import operator
import threading
import unittest

import six

from pyface.ui.qt4.util.gui_test_assistant import GuiTestAssistant
from traits.api import HasStrictTraits, Instance, List, on_trait_change

from traits_futures.api import (
    CallFuture, FutureState, TraitsExecutor,
    CANCELLED, CANCELLING, EXECUTING, FAILED, COMPLETED, WAITING,
)
from traits_futures.tests.common_future_tests import CommonFutureTests
from traits_futures.tests.lazy_message_router import LazyMessageRouter


#: Number of workers for the thread pool.
WORKERS = 4

#: Timeout for blocking operations, in seconds.
TIMEOUT = 10.0


class Listener(HasStrictTraits):
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
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=WORKERS)
        self.executor = TraitsExecutor(thread_pool=self.thread_pool)

    def tearDown(self):
        self.halt_executor(self.executor)
        self.thread_pool.shutdown()
        GuiTestAssistant.tearDown(self)

    def test_successful_call(self):
        future = self.executor.submit_call(pow, 2, 3)
        listener = Listener(future=future)

        self.wait_for_completion(future)

        self.assertResult(future, 8)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, COMPLETED],
        )

    def test_failed_call(self):
        future = self.executor.submit_call(operator.floordiv, 1, 0)
        listener = Listener(future=future)

        self.wait_for_completion(future)

        self.assertNoResult(future)
        self.assertException(future, ZeroDivisionError)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, FAILED],
        )

    def test_cancellation_before_execution(self):
        future = self.executor.submit_call(pow, 2, 3)
        listener = Listener(future=future)

        self.assertTrue(future.cancellable)
        future.cancel()
        self.wait_for_completion(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    # Helpers

    def halt_executor(self, executor):
        """
        Stop the executor, and wait until it reaches STOPPED state.
        """
        executor.stop()
        with self.event_loop_until_condition(lambda: executor.stopped):
            pass

    def wait_for_completion(self, future):
        with self.event_loop_until_condition(lambda: future.done):
            pass

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


class TestBackgroundCallNoUI(unittest.TestCase):
    def setUp(self):
        self.router = LazyMessageRouter()
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=WORKERS)
        self.executor = TraitsExecutor(
            thread_pool=self.thread_pool,
            _message_router=self.router
        )

    def tearDown(self):
        self.halt_executor(self.executor)
        self.thread_pool.shutdown()

    def test_successful_call(self):
        future = self.executor.submit_call(pow, 2, 3)
        listener = Listener(future=future)

        self.wait_for_completion(future)

        self.assertResult(future, 8)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, COMPLETED],
        )

    def test_failed_call(self):
        future = self.executor.submit_call(operator.floordiv, 1, 0)
        listener = Listener(future=future)

        self.wait_for_completion(future)

        self.assertNoResult(future)
        self.assertException(future, ZeroDivisionError)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, FAILED],
        )

    def test_cancellation_before_execution(self):
        # This test is delicate - we want to simulate a particular race
        # condition. Specifically, we want to exercise the code branch where a
        # STARTED message arrives while the future is in CANCELLING state. But
        # if we cancel too soon, the background job will send INTERRUPTED
        # instead of STARTED. So we wait until we're sure that the background
        # job has sent the STARTED message, then cancel _before_ we receive and
        # process that message.
        event = threading.Event()

        future = self.executor.submit_call(event.set)
        listener = Listener(future=future)

        self.assertTrue(event.wait(timeout=TIMEOUT))
        self.assertTrue(future.cancellable)
        future.cancel()
        self.wait_for_completion(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_background_job_starts(self):
        # Not quite the same as the test above: that one lets the background
        # job start executing, but cancels before we receive any messages from
        # it. This test cancels before the background job begins execution at
        # all, so exercises a different code path in the background job code.
        with self.blocked_thread_pool():
            future = self.executor.submit_call(pow, 2, 3)
            listener = Listener(future=future)
            self.assertTrue(future.cancellable)
            future.cancel()

        self.wait_for_completion(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_success(self):
        future = self.executor.submit_call(pow, 2, 3)
        listener = Listener(future=future)

        self.wait_for_state(future, EXECUTING)
        self.assertTrue(future.cancellable)
        future.cancel()
        self.wait_for_completion(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_failure(self):
        future = self.executor.submit_call(operator.floordiv, 1, 0)
        listener = Listener(future=future)

        self.wait_for_state(future, EXECUTING)
        self.assertTrue(future.cancellable)
        future.cancel()
        self.wait_for_completion(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancel_after_success(self):
        future = self.executor.submit_call(pow, 2, 3)
        listener = Listener(future=future)

        self.wait_for_completion(future)

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()
        self.assertResult(future, 8)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, COMPLETED],
        )

    def test_cancel_after_failure(self):
        future = self.executor.submit_call(operator.floordiv, 1, 0)
        listener = Listener(future=future)

        self.wait_for_completion(future)

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()
        self.assertNoResult(future)
        self.assertException(future, ZeroDivisionError)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, FAILED],
        )

    def test_double_cancel(self):
        future = self.executor.submit_call(pow, 2, 3)
        listener = Listener(future=future)

        self.assertTrue(future.cancellable)
        future.cancel()
        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

        self.wait_for_completion(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_double_cancel_variant(self):
        future = self.executor.submit_call(pow, 2, 3)
        listener = Listener(future=future)

        self.assertTrue(future.cancellable)
        future.cancel()
        self.wait_for_state(future, CANCELLING)
        with self.assertRaises(RuntimeError):
            self.assertFalse(future.cancellable)
            future.cancel()
        self.wait_for_completion(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_background_call_keyword_arguments(self):
        future = self.executor.submit_call(int, "10101", base=2)

        self.wait_for_completion(future)

        self.assertResult(future, 21)

    def test_completed_success(self):
        future = self.executor.submit_call(pow, 2, 3)

        self.assertFalse(future.done)
        self.wait_for_completion(future)
        self.assertTrue(future.done)

    def test_completed_failure(self):
        future = self.executor.submit_call(operator.floordiv, 1, 0)

        self.assertFalse(future.done)
        self.wait_for_completion(future)
        self.assertTrue(future.done)

    def test_completed_cancelled(self):
        future = self.executor.submit_call(pow, 2, 3)

        self.assertFalse(future.done)
        future.cancel()
        self.assertFalse(future.done)
        self.wait_for_state(future, CANCELLING)
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
        Stop the executor, and wait until it reaches STOPPED state.
        """
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
