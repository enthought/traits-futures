import threading
import unittest

from six.moves import queue

from traits_futures.job import (
    background_job,
    Job,
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


def fail_with_exception(exc_type):
    raise exc_type()


class TestJob(unittest.TestCase):
    def setUp(self):
        self.results_queue = DummyQueue()
        self.cancel_event = threading.Event()

    def test_successful_run(self):
        job = Job(callable=square, args=(11,))
        job_handle, runner = job.prepare(
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
        job = Job(callable=fail_with_exception, args=(ZeroDivisionError,))
        job_handle, runner = job.prepare(
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
        self.assertIn("ZeroDivisionError", exc_tb)

    def test_cancelled_run(self):
        job = Job(callable=fail_with_exception, args=(ZeroDivisionError,))
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

        for job_id, message in messages:
            job_handle.process_message(message)

        self.assertIsNone(job_handle.result)
        self.assertIsNone(job_handle.exception)
        self.assertEqual(job_handle.state, CANCELLED)

    def test_cancellable(self):
        job = Job(callable=square, args=(13,))
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
        job = Job(callable=square, args=(13,))
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
        job = Job(callable=square, args=(13,))
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

    def test_background_job(self):
        job = background_job(int, "1101", base=2)
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

    def test_background_job_multiple_arguments(self):
        job = background_job(pow, 3, 5, 7)
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
            job_id, (msg_type, msg_args) = msg
            messages.append(msg)
            if msg_type in (INTERRUPTED, RAISED, RETURNED):
                return messages
