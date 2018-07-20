import unittest

import concurrent.futures
from six.moves import queue

from traits.api import HasStrictTraits, Instance, List, on_trait_change

from traits_futures.job import (
    Job,
    JobHandle,
    WAITING,
    EXECUTING,
    CANCELLING,
    SUCCEEDED,
    FAILED,
    CANCELLED,
)
from traits_futures.job_controller import JobController


def square(n):
    return n * n


def divide_by_zero():
    3 / 0


class Listener(HasStrictTraits):
    job = Instance(JobHandle)

    results = List

    exceptions = List

    states = List

    @on_trait_change("job:result")
    def record_result(self, result):
        self.results.append(result)

    @on_trait_change("job:exception")
    def record_exception(self, exception):
        self.exceptions.append(exception)

    @on_trait_change("job:state")
    def record_state_change(self, obj, name, old_state, new_state):
        if not self.states:
            self.states.append(old_state)
        else:
            assert old_state == self.states[-1]
        self.states.append(new_state)


class TestJobControllerNoUI(unittest.TestCase):
    def setUp(self):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.results_queue = queue.Queue()
        self.controller = JobController(
            executor=self.executor,
            _results_queue=self.results_queue,
        )

    def tearDown(self):
        self.executor.shutdown()

    def test_submit_simple_job(self):
        job = Job(callable=square, args=(10,))
        job_handle = self.controller.submit(job)
        listener = Listener(job=job_handle)

        self.controller.run_loop()

        self.assertEqual(listener.results, [100])
        self.assertEqual(listener.exceptions, [])
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, SUCCEEDED],
        )

    def test_submit_failing_job(self):
        job = Job(callable=divide_by_zero)
        job_handle = self.controller.submit(job)
        listener = Listener(job=job_handle)

        self.controller.run_loop()

        self.assertEqual(listener.results, [])
        self.assertEqual(len(listener.exceptions), 1)
        exc_type, exc_value, exc_tb = listener.exceptions[0]
        self.assertIn("ZeroDivisionError", exc_type)
        self.assertIn("by zero", exc_value)
        self.assertIn("ZeroDivisionError", exc_tb)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, FAILED],
        )

    def test_cancel(self):
        job = Job(callable=square, args=(10,))
        job_handle = self.controller.submit(job)
        listener = Listener(job=job_handle)

        job_handle.cancel()
        self.controller.run_loop()

        self.assertEqual(listener.results, [])
        self.assertEqual(listener.exceptions, [])
        # Here we cancelled before processing any of the
        # messages received, so we don't see the "EXECUTING" state.
        self.assertEqual(
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_cancel_after_start(self):
        job = Job(callable=square, args=(3,))
        job_handle = self.controller.submit(job)
        listener = Listener(job=job_handle)

        self.controller.run_loop_until(lambda: job_handle.state == EXECUTING)
        job_handle.cancel()
        self.controller.run_loop()

        self.assertEqual(listener.results, [])
        self.assertEqual(listener.exceptions, [])
        # Here we cancelled before processing any of the
        # messages received, so we don't see the "EXECUTING" state.
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancel_failing(self):
        job = Job(callable=divide_by_zero)
        job_handle = self.controller.submit(job)
        listener = Listener(job=job_handle)

        job_handle.cancel()
        self.controller.run_loop()

        self.assertEqual(listener.results, [])
        self.assertEqual(listener.exceptions, [])
        self.assertEqual(
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_cancel_failing_after_start(self):
        job = Job(callable=divide_by_zero)
        job_handle = self.controller.submit(job)
        listener = Listener(job=job_handle)

        self.controller.run_loop_until(lambda: job_handle.state == EXECUTING)
        job_handle.cancel()
        self.controller.run_loop()

        self.assertEqual(listener.results, [])
        self.assertEqual(listener.exceptions, [])
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )
