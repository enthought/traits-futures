import threading
import unittest

from six.moves import queue

from traits_futures.job import (
    Job,
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

    def _get_messages(self):
        messages = []
        while True:
            msg = self.results_queue.get()
            job_id, (msg_type, msg_args) = msg
            messages.append(msg)
            if msg_type in (INTERRUPTED, RAISED, RETURNED):
                return messages
