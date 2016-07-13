import Queue as queue
import unittest

from traits_futures.job import Job, QUEUED
from traits_futures.job_runner import (
    JobRunner,
    INTERRUPTED,
    RAISED,
    RETURNED,
    STARTING,
)


# Timeout (in seconds) to make sure that tests don't run forever as a result of
# programming errors.
SAFETY_TIMEOUT = 10.0


def square(n):
    return n * n


def fail_with_exception(exc_type):
    raise exc_type()


class TestJobRunner(unittest.TestCase):
    def setUp(self):
        self.results_queue = queue.Queue()

    def test_successful_run(self):
        job = Job(job=square, args=(11,))

        runner = JobRunner(
            job=job,
            job_id=1729,
            results_queue=self.results_queue,
        )
        job.state = QUEUED

        runner()

        # Get messages.
        messages = self._get_messages()

        # Check that there are no more messages.
        with self.assertRaises(queue.Empty):
            self.results_queue.get(timeout=0.1)

        self.assertEqual(
            messages,
            [
                (1729, STARTING, None),
                (1729, RETURNED, 121),
            ],
        )

    def test_failed_run(self):
        job = Job(job=fail_with_exception, args=(ZeroDivisionError,))
        runner = JobRunner(
            job=job,
            job_id=1729,
            results_queue=self.results_queue,
        )
        job.state = QUEUED

        runner()

        messages = self._get_messages()

        # Check that there are no more messages.
        with self.assertRaises(queue.Empty):
            self.results_queue.get(timeout=0.1)

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], (1729, STARTING, None))
        self.assertEqual(messages[1][:2], (1729, RAISED))
        self.assertIn("ZeroDivisionError", messages[1][2])

    def test_cancelled_run(self):
        job = Job(job=fail_with_exception, args=(ZeroDivisionError,))
        runner = JobRunner(
            job=job,
            job_id=1729,
            results_queue=self.results_queue,
        )
        job.state = QUEUED

        job.cancel()

        runner()

        messages = self._get_messages()
        self.assertEqual(
            messages,
            [(1729, INTERRUPTED, None)],
        )

    def _get_messages(self):
        messages = []
        while True:
            message = self.results_queue.get(timeout=SAFETY_TIMEOUT)
            messages.append(message)
            if message[1] in (INTERRUPTED, RAISED, RETURNED):
                return messages
