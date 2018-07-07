"""
Tests for the background iteration functionality.
"""
import contextlib
import threading
import unittest

import concurrent.futures
from six.moves import queue

from traits.api import HasStrictTraits, Instance, List, on_trait_change

from traits_futures.iteration import (
    background_iteration,
    CANCELLING,
    CANCELLED,
    COMPLETED,
    EXECUTING,
    FAILED,
    IterationFuture,
    SETUP_FAILED,
    WAITING,
)
from traits_futures.job_controller import JobController


# Number of executor workers used in the test.
WORKERS = 4


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

    #: Collected results.
    results = List

    @on_trait_change('future:result')
    def record_iteration_result(self, result):
        self.results.append(result)


class TestIterationNoUI(unittest.TestCase):
    def setUp(self):
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=WORKERS)
        self.results_queue = queue.Queue()
        self.controller = JobController(
            executor=self.executor,
            _results_queue=self.results_queue,
        )

    def tearDown(self):
        self.executor.shutdown()

    def test_background_iteration(self):
        # A simple case.
        iteration = background_iteration(range, 10, 15)
        iteration_future = self.controller.submit(iteration)
        listener = Listener(future=iteration_future)

        self.controller.run_loop()

        self.assertEqual(iteration_future.state, COMPLETED)
        self.assertEqual(
            listener.results,
            list(range(10, 15)),
        )
        self.assertEqual(iteration_future.exception, None)

    def test_bad_iteration_setup(self):
        # Deliberately passing a callable that returns
        # something non-iterable.
        iteration = background_iteration(pow, 2, 5)
        iteration_future = self.controller.submit(iteration)

        self.controller.run_loop()

        self.assertEqual(iteration_future.state, SETUP_FAILED)
        exc_type, exc_value, exc_traceback = iteration_future.exception
        self.assertIn("TypeError", exc_type)
        self.assertIn("object is not iterable", exc_value)
        self.assertIn("traits_futures", exc_traceback)
        self.assertIn("iteration.py", exc_traceback)

    def test_failing_iteration(self):
        iteration = background_iteration(reciprocals, start=-3, stop=3)
        iteration_future = self.controller.submit(iteration)

        self.controller.run_loop()

        self.assertEqual(iteration_future.state, FAILED)
        exc_type, exc_value, exc_traceback = iteration_future.exception
        self.assertIn("ZeroDivisionError", exc_type)
        self.assertIn("division by zero", exc_value)
        self.assertIn("traits_futures", exc_traceback)
        self.assertIn("iteration.py", exc_traceback)

    def test_starting(self):
        iteration = background_iteration(map, lambda x: x*x, range(10))
        iteration_future = self.controller.submit(iteration)
        listener = Listener(future=iteration_future)

        self.assertEqual(iteration_future.state, WAITING)

        self.controller.run_loop_until(
            lambda: iteration_future.state == EXECUTING
        )
        self.assertEqual(iteration_future.state, EXECUTING)
        self.assertIsNone(iteration_future.exception)

        self.controller.run_loop()
        self.assertEqual(iteration_future.state, COMPLETED)
        self.assertIsNone(iteration_future.exception)

        self.assertEqual(
            listener.results,
            [x*x for x in range(10)],
        )

    def test_cancel_before_start(self):
        with self.blocked_executor():
            iteration = background_iteration(squares, 0, 10)
            future = self.controller.submit(iteration)
            listener = Listener(future=future)
            future.cancel()

        self.assertEqual(future.state, CANCELLING)
        self.controller.run_loop()
        self.assertEqual(future.state, CANCELLED)

        self.assertIsNone(future.exception)
        self.assertEqual(listener.results, [])

    def test_cancel_after_start(self):
        iteration = background_iteration(squares, 0, 10)
        future = self.controller.submit(iteration)
        listener = Listener(future=future)

        self.assertEqual(future.state, WAITING)
        self.controller.run_loop_until(
            lambda: len(listener.results) > 0
        )
        self.assertEqual(future.state, EXECUTING)
        future.cancel()
        self.assertEqual(future.state, CANCELLING)
        self.controller.run_loop()
        self.assertEqual(future.state, CANCELLED)
        self.assertIsNone(future.exception)
        self.assertEqual(listener.results, [0])

    def test_cancel_bad_job(self):
        iteration = background_iteration(pow, 10, 3)
        future = self.controller.submit(iteration)
        future.cancel()

        self.assertEqual(future.state, CANCELLING)

        self.controller.run_loop()

        self.assertEqual(future.state, CANCELLED)
        self.assertIsNone(future.exception)

    def test_double_cancel(self):
        iteration = background_iteration(squares, 0, 10)
        future = self.controller.submit(iteration)

        self.assertTrue(future.cancellable)
        future.cancel()
        self.assertFalse(future.cancellable)

        with self.assertRaises(RuntimeError):
            future.cancel()

    def test_completed_cancel(self):
        iteration = background_iteration(squares, 0, 10)
        future = self.controller.submit(iteration)

        self.controller.run_loop()

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

    def test_completed_normal_completion(self):
        iteration = background_iteration(squares, 0, 10)
        future = self.controller.submit(iteration)

        self.assertFalse(future.completed)
        self.controller.run_loop()
        self.assertTrue(future.completed)

    def test_completed_exception(self):
        iteration = background_iteration(reciprocals, -5, 5)
        future = self.controller.submit(iteration)

        self.assertFalse(future.completed)
        self.controller.run_loop()
        self.assertTrue(future.completed)

    def test_completed_bad_iterable(self):
        iteration = background_iteration(pow, 2, 3)
        future = self.controller.submit(iteration)

        self.assertFalse(future.completed)
        self.controller.run_loop()
        self.assertTrue(future.completed)

    def test_completed_cancelled(self):
        iteration = background_iteration(squares, 0, 10)
        future = self.controller.submit(iteration)

        self.assertFalse(future.completed)
        future.cancel()
        self.assertFalse(future.completed)
        self.controller.run_loop()
        self.assertTrue(future.completed)

    # Helper functions

    @contextlib.contextmanager
    def blocked_executor(self):
        """
        Context manager to temporarily block the executor.
        """
        events = [threading.Event() for _ in range(WORKERS)]
        for event in events:
            self.executor.submit(event.wait)
        try:
            yield
        finally:
            for event in events:
                event.set()
