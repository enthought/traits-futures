from __future__ import absolute_import, print_function, unicode_literals

import threading
import unittest

from six.moves import queue

from traits_futures.background_call import (
    background_call,
    BackgroundCall,
    CANCELLED,
    INTERRUPTED,
    RAISED,
    RETURNED,
    STARTED,
)


class DummyQueue(object):
    """
    Dummy object with queue interface, for testing purposes.
    """
    def __init__(self):
        self.messages = []

    def put(self, message):
        self.messages.append(message)

    def get(self):
        if self.messages:
            return self.messages.pop(0)
        else:
            raise queue.Empty


def square(n):
    return n * n


def divide_by_zero():
    5 / 0


class TestBackgroundCall(unittest.TestCase):
    def setUp(self):
        self.results_queue = DummyQueue()
        self.cancel_event = threading.Event()

    def test_successful_run(self):
        job = BackgroundCall(callable=square, args=(11,))
        _, runner = job.prepare(
            job_id=1729,
            cancel_event=self.cancel_event,
            results_queue=self.results_queue,
        )

        runner()
        messages = self._get_messages()

        # Check that there are no more messages.
        with self.assertRaises(queue.Empty):
            self.results_queue.get()

        self.assertEqual(
            messages,
            [
                (1729, (STARTED, None)),
                (1729, (RETURNED, 121)),
            ],
        )

    def test_failed_run(self):
        job = BackgroundCall(callable=divide_by_zero)
        _, runner = job.prepare(
            job_id=1729,
            cancel_event=self.cancel_event,
            results_queue=self.results_queue,
        )

        runner()
        messages = self._get_messages()

        # Check that there are no more messages.
        with self.assertRaises(queue.Empty):
            self.results_queue.get()

        self.assertEqual(len(messages), 2)
        self.assertEqual(
            messages[0],
            (1729, (STARTED, None)),
        )
        job_id, (msg_type, msg_args) = messages[1]
        self.assertEqual(job_id, 1729)
        self.assertEqual(msg_type, RAISED)
        exc_type, exc_value, exc_tb = msg_args
        self.assertIn("ZeroDivisionError", exc_type)
        self.assertIn("by zero", exc_value)
        self.assertIn("ZeroDivisionError", exc_tb)

    def test_cancelled_run(self):
        job = BackgroundCall(callable=divide_by_zero)
        job_handle, runner = job.prepare(
            job_id=1729,
            cancel_event=self.cancel_event,
            results_queue=self.results_queue,
        )

        job_handle.cancel()

        runner()
        messages = self._get_messages()

        # Check that there are no more messages.
        with self.assertRaises(queue.Empty):
            self.results_queue.get()

        self.assertEqual(
            messages,
            [(1729, (INTERRUPTED, None))],
        )

        for _, message in messages:
            job_handle.process_message(message)

        self.assertIsNone(job_handle.result)
        self.assertIsNone(job_handle.exception)
        self.assertEqual(job_handle.state, CANCELLED)

    def test_cancellable(self):
        job = BackgroundCall(callable=square, args=(13,))
        job_handle, runner = job.prepare(
            job_id=47,
            cancel_event=self.cancel_event,
            results_queue=self.results_queue,
        )
        runner()

        self.assertTrue(job_handle.cancellable)
        for job_id, message in self._get_messages():
            self.assertEqual(job_id, 47)
            job_handle.process_message(message)

        self.assertFalse(job_handle.cancellable)

    def test_cancel_twice(self):
        job = BackgroundCall(callable=square, args=(13,))
        job_handle, runner = job.prepare(
            job_id=47,
            cancel_event=self.cancel_event,
            results_queue=self.results_queue,
        )
        runner()

        self.assertTrue(job_handle.cancellable)
        job_handle.cancel()
        self.assertFalse(job_handle.cancellable)
        with self.assertRaises(RuntimeError):
            job_handle.cancel()

    def test_cancel_completed(self):
        job = BackgroundCall(callable=square, args=(13,))
        job_handle, runner = job.prepare(
            job_id=47,
            cancel_event=self.cancel_event,
            results_queue=self.results_queue,
        )
        runner()

        for job_id, message in self._get_messages():
            self.assertEqual(job_id, 47)
            job_handle.process_message(message)

        self.assertFalse(job_handle.cancellable)
        with self.assertRaises(RuntimeError):
            job_handle.cancel()

    def test_background_call(self):
        job = background_call(int, "1101", base=2)
        job_handle, runner = job.prepare(
            job_id=47,
            cancel_event=self.cancel_event,
            results_queue=self.results_queue,
        )
        runner()

        for job_id, message in self._get_messages():
            self.assertEqual(job_id, 47)
            job_handle.process_message(message)

        self.assertEqual(job_handle.result, 13)

    def test_background_call_multiple_arguments(self):
        job = background_call(pow, 3, 5, 7)
        job_handle, runner = job.prepare(
            job_id=47,
            cancel_event=self.cancel_event,
            results_queue=self.results_queue,
        )
        runner()

        for job_id, message in self._get_messages():
            self.assertEqual(job_id, 47)
            job_handle.process_message(message)

        self.assertEqual(job_handle.result, 5)

    def _get_messages(self):
        messages = []
        while True:
            msg = self.results_queue.get()
            _, (msg_type, _) = msg
            messages.append(msg)
            if msg_type in (INTERRUPTED, RAISED, RETURNED):
                return messages
