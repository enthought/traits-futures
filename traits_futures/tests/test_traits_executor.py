"""
Tests for the TraitsExecutor class.
"""
from __future__ import absolute_import, print_function, unicode_literals

import concurrent.futures
import contextlib
import threading
import unittest

from traits.api import HasStrictTraits, Instance, List, on_trait_change

from traits_futures.api import (
    CANCELLED,
    CANCELLING,
    EXECUTING,
    TraitsExecutor,
    ExecutorState,
    RUNNING,
    STOPPING,
    STOPPED,
)
from traits_futures.toolkit_support import gui_test_assistant_class

GuiTestAssistant = gui_test_assistant_class()


class Listener(HasStrictTraits):
    #: Executor that we're listening to.
    executor = Instance(TraitsExecutor)

    #: List of states of that executor.
    states = List(ExecutorState)

    @on_trait_change('executor:state')
    def record_state_change(self, obj, name, old_state, new_state):
        if not self.states:
            # On the first state change, record the initial state as well as
            # the new one.
            self.states.append(old_state)
        self.states.append(new_state)


class TestTraitsExecutor(GuiTestAssistant, unittest.TestCase):
    def setUp(self):
        GuiTestAssistant.setUp(self)
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=4)

    def tearDown(self):
        if hasattr(self, "executor"):
            self.executor.stop()
            self.wait_for_stop(self.executor)
            del self.executor
        self.thread_pool.shutdown()
        GuiTestAssistant.tearDown(self)

    def test_stop_method(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        listener = Listener(executor=executor)

        with self.long_running_task(executor):
            self.assertEqual(executor.state, RUNNING)
            executor.stop()
            self.assertEqual(executor.state, STOPPING)

        self.wait_for_stop(executor)
        self.assertEqual(executor.state, STOPPED)
        self.assertEqual(listener.states, [RUNNING, STOPPING, STOPPED])

    def test_stop_method_with_no_jobs(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        listener = Listener(executor=executor)

        self.assertEqual(executor.state, RUNNING)
        executor.stop()
        self.wait_for_stop(executor)
        self.assertEqual(executor.state, STOPPED)
        self.assertEqual(listener.states, [RUNNING, STOPPING, STOPPED])

    def test_stop_method_raises_unless_running(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)

        with self.long_running_task(executor):
            self.assertEqual(executor.state, RUNNING)
            executor.stop()

            # Raises if in STOPPING mode.
            self.assertEqual(executor.state, STOPPING)
            with self.assertRaises(RuntimeError):
                executor.stop()

        self.wait_for_stop(executor)
        # Raises if in STOPPED mode.
        self.assertEqual(executor.state, STOPPED)
        with self.assertRaises(RuntimeError):
            executor.stop()

    def test_cant_submit_new_unless_running(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        with self.long_running_task(executor):
            executor.stop()
            self.assertEqual(executor.state, STOPPING)

            with self.assertRaises(RuntimeError):
                executor.submit_call(len, (1, 2, 3))

        self.wait_for_stop(executor)
        self.assertEqual(executor.state, STOPPED)
        with self.assertRaises(RuntimeError):
            executor.submit_call(int)

    def test_stop_cancels_running_futures(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        with self.long_running_task(executor) as future:
            self.wait_until_executing(future)

            self.assertEqual(future.state, EXECUTING)
            executor.stop()
            self.assertEqual(future.state, CANCELLING)

        self.wait_for_future(future)
        self.assertEqual(future.state, CANCELLED)

    def test_running(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        self.assertTrue(executor.running)

        with self.long_running_task(executor):
            self.assertTrue(executor.running)
            executor.stop()
            self.assertFalse(executor.running)

        self.wait_for_stop(executor)
        self.assertFalse(executor.running)

    def test_stopped(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        self.assertFalse(executor.stopped)

        with self.long_running_task(executor):
            self.assertFalse(executor.stopped)
            executor.stop()
            self.assertFalse(executor.stopped)

        self.wait_for_stop(executor)
        self.assertTrue(executor.stopped)

    def test_owned_thread_pool(self):
        executor = TraitsExecutor()
        thread_pool = executor._thread_pool

        executor.stop()
        self.wait_for_stop(executor)

        # Check that the internally-created thread pool has been shut down.
        with self.assertRaises(RuntimeError):
            thread_pool.submit(int)

    def test_shared_thread_pool(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        executor.stop()
        self.wait_for_stop(executor)

        # Check that the the shared thread pool is still available.
        future = self.thread_pool.submit(int)
        self.assertEqual(future.result(), 0)

    def test_submit_call(self):
        def test_call(*args, **kwds):
            return args, kwds

        self.executor = TraitsExecutor(thread_pool=self.thread_pool)
        future = self.executor.submit_call(
            test_call, "arg1", "arg2", kwd1="kwd1", kwd2="kwd2")

        self.wait_for_future(future)

        self.assertEqual(
            future.result,
            (
                ("arg1", "arg2"),
                {"kwd1": "kwd1", "kwd2": "kwd2"},
            ),
        )

    def test_submit_iteration(self):
        def test_iteration(*args, **kwargs):
            yield args
            yield kwargs

        self.executor = TraitsExecutor(thread_pool=self.thread_pool)
        future = self.executor.submit_iteration(
            test_iteration, "arg1", "arg2", kwd1="kwd1", kwd2="kwd2")

        results = []
        future.on_trait_change(lambda result: results.append(result), 'result')

        self.wait_for_future(future)
        self.assertEqual(
            results,
            [
                ("arg1", "arg2"),
                {"kwd1": "kwd1", "kwd2": "kwd2"},
            ],
        )

    def test_submit_progress(self):
        def test_progress(arg1, arg2, kwd1, kwd2, progress):
            return arg1, arg2, kwd1, kwd2

        self.executor = TraitsExecutor(thread_pool=self.thread_pool)
        future = self.executor.submit_progress(
            test_progress, "arg1", "arg2", kwd1="kwd1", kwd2="kwd2")

        self.wait_for_future(future)

        self.assertEqual(
            future.result,
            ("arg1", "arg2", "kwd1", "kwd2"),
        )

    # Helper methods and assertions ###########################################

    def wait_for_stop(self, executor):
        """"
        Wait for the executor to reach STOPPED state.
        """
        self.run_until_condition(
            executor, "stopped", lambda executor: executor.stopped)

    def wait_until_executing(self, future):
        """
        Wait until the given future is executing.
        """
        self.run_until_condition(
            future, "state", lambda future: future.state == EXECUTING)

    def wait_for_future(self, future):
        """
        Wait until the given future completes.
        """
        self.run_until_condition(future, "done", lambda future: future.done)

    @contextlib.contextmanager
    def long_running_task(self, executor):
        """
        Simulate a long-running task being submitted to the executor.

        The task finishes on exit of the with block.
        """
        event = threading.Event()
        try:
            yield executor.submit_call(event.wait)
        finally:
            event.set()
