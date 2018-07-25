from __future__ import absolute_import, print_function, unicode_literals

import collections
import contextlib
import itertools
import operator
import threading
import unittest

import concurrent.futures
import six
from six.moves import queue

from pyface.ui.qt4.util.gui_test_assistant import GuiTestAssistant
from traits.api import (
    Any, Event, HasStrictTraits, Instance, Int, List, on_trait_change, Tuple)

from traits_futures.api import (
    background_call, CallFuture, CallFutureState, TraitsExecutor,
    CANCELLED, CANCELLING, EXECUTING, FAILED, SUCCEEDED, WAITING,
)


#: Number of workers for the test executors.
WORKERS = 4

#: Timeout for queue.get operations, in seconds.
TIMEOUT = 10.0


class LazyMessageSender(object):
    def __init__(self, sender_id, message_queue):
        self.sender_id = sender_id
        self.message_queue = message_queue

    def connect(self):
        pass

    def disconnect(self):
        pass

    def send(self, message):
        self.message_queue.put((self.sender_id, message))


class LazyMessageReceiver(HasStrictTraits):
    #: Event fired whenever a message is received. The first part of
    #: the received message is the sender id. The second part is
    #: the message itself.
    received = Event(Tuple(Int, Any))

    #: Internal queue for messages from workers.
    _message_queue = Any

    #: Source of task ids for new tasks.
    _sender_ids = Instance(collections.Iterator)

    def __message_queue_default(self):
        return queue.Queue()

    def __sender_ids_default(self):
        return itertools.count()

    def sender(self):
        """
        Create a new LazyMessageSender for this receiver.
        """
        sender_id = next(self._sender_ids)
        sender = LazyMessageSender(
            sender_id=sender_id,
            message_queue=self._message_queue,
        )
        return sender_id, sender

    def send_until(self, condition):
        while not condition():
            message = self._message_queue.get(timeout=TIMEOUT)
            self.received = message


class Listener(HasStrictTraits):
    #: Future that we're listening to.
    future = Instance(CallFuture)

    #: List of states of that future.
    states = List(CallFutureState)

    @on_trait_change("future:state")
    def record_state_change(self, obj, name, old_state, new_state):
        if not self.states:
            # On the first state change, record the initial state as well as
            # the new one.
            self.states.append(old_state)
        self.states.append(new_state)


class TestBackgroundCall(GuiTestAssistant, unittest.TestCase):
    def setUp(self):
        GuiTestAssistant.setUp(self)
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=WORKERS)
        self.controller = TraitsExecutor(executor=self.executor)

    def tearDown(self):
        self.executor.shutdown()
        GuiTestAssistant.tearDown(self)

    def test_successful_call(self):
        job = background_call(pow, 2, 3)
        future = self.controller.submit(job)
        listener = Listener(future=future)

        self.wait_for_completion(future)

        self.assertResult(future, 8)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, SUCCEEDED],
        )

    def test_failed_call(self):
        job = background_call(operator.floordiv, 1, 0)
        future = self.controller.submit(job)
        listener = Listener(future=future)

        self.wait_for_completion(future)

        self.assertNoResult(future)
        self.assertException(future, ZeroDivisionError)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, FAILED],
        )

    def test_cancellation_before_execution(self):
        job = background_call(pow, 2, 3)
        future = self.controller.submit(job)
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

    def wait_for_completion(self, future):
        with self.event_loop_until_condition(lambda: future.completed):
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
        self.receiver = LazyMessageReceiver()
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=WORKERS)
        self.controller = TraitsExecutor(
            executor=self.executor,
            _message_receiver=self.receiver
        )

    def tearDown(self):
        self.executor.shutdown()

    def test_successful_call(self):
        job = background_call(pow, 2, 3)
        future = self.controller.submit(job)
        listener = Listener(future=future)

        self.receiver.send_until(lambda: future.completed)

        self.assertResult(future, 8)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, SUCCEEDED],
        )

    def test_failed_call(self):
        job = background_call(operator.floordiv, 1, 0)
        future = self.controller.submit(job)
        listener = Listener(future=future)

        self.receiver.send_until(lambda: future.completed)

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

        job = background_call(event.set)
        future = self.controller.submit(job)
        listener = Listener(future=future)

        event.wait()
        self.assertTrue(future.cancellable)
        future.cancel()
        self.receiver.send_until(lambda: future.completed)

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
        job = background_call(pow, 2, 3)
        with self.blocked_executor():
            future = self.controller.submit(job)
            listener = Listener(future=future)
            self.assertTrue(future.cancellable)
            future.cancel()

        self.receiver.send_until(lambda: future.completed)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_success(self):
        job = background_call(pow, 2, 3)
        future = self.controller.submit(job)
        listener = Listener(future=future)

        self.receiver.send_until(lambda: future.state == EXECUTING)
        self.assertTrue(future.cancellable)
        future.cancel()
        self.receiver.send_until(lambda: future.completed)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_failure(self):
        job = background_call(operator.floordiv, 1, 0)
        future = self.controller.submit(job)
        listener = Listener(future=future)

        self.receiver.send_until(lambda: future.state == EXECUTING)
        self.assertTrue(future.cancellable)
        future.cancel()
        self.receiver.send_until(lambda: future.completed)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancel_after_success(self):
        job = background_call(pow, 2, 3)
        future = self.controller.submit(job)
        listener = Listener(future=future)

        self.receiver.send_until(lambda: future.completed)

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()
        self.assertResult(future, 8)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, SUCCEEDED],
        )

    def test_cancel_after_failure(self):
        job = background_call(operator.floordiv, 1, 0)
        future = self.controller.submit(job)
        listener = Listener(future=future)

        self.receiver.send_until(lambda: future.completed)

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
        job = background_call(pow, 2, 3)
        future = self.controller.submit(job)
        listener = Listener(future=future)

        self.assertTrue(future.cancellable)
        future.cancel()
        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

        self.receiver.send_until(lambda: future.completed)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_double_cancel_variant(self):
        job = background_call(pow, 2, 3)
        future = self.controller.submit(job)
        listener = Listener(future=future)

        self.assertTrue(future.cancellable)
        future.cancel()
        self.receiver.send_until(lambda: future.state == CANCELLING)
        with self.assertRaises(RuntimeError):
            self.assertFalse(future.cancellable)
            future.cancel()
        self.receiver.send_until(lambda: future.completed)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_background_call_keyword_arguments(self):
        job = background_call(int, "10101", base=2)
        future = self.controller.submit(job)

        self.receiver.send_until(lambda: future.completed)

        self.assertResult(future, 21)

    def test_completed_success(self):
        job = background_call(pow, 2, 3)
        future = self.controller.submit(job)

        self.assertFalse(future.completed)
        self.receiver.send_until(lambda: future.completed)
        self.assertTrue(future.completed)

    def test_completed_failure(self):
        job = background_call(operator.floordiv, 1, 0)
        future = self.controller.submit(job)

        self.assertFalse(future.completed)
        self.receiver.send_until(lambda: future.completed)
        self.assertTrue(future.completed)

    def test_completed_cancelled(self):
        job = background_call(pow, 2, 3)
        future = self.controller.submit(job)

        self.assertFalse(future.completed)
        future.cancel()
        self.assertFalse(future.completed)
        self.receiver.send_until(lambda: future.state == CANCELLING)
        self.assertFalse(future.completed)
        self.receiver.send_until(lambda: future.completed)
        self.assertTrue(future.completed)

    # Helper functions

    @contextlib.contextmanager
    def blocked_executor(self):
        """
        Context manager to temporarily block the executor.
        """
        event = threading.Event()
        for _ in range(WORKERS):
            self.executor.submit(event.wait)
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
