"""
Tests for the TraitsExecutor class.
"""
from __future__ import absolute_import, print_function, unicode_literals

import concurrent.futures
import contextlib
import threading
import unittest

from pyface.ui.qt4.util.gui_test_assistant import GuiTestAssistant
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
        self.thread_pool.shutdown()
        GuiTestAssistant.tearDown(self)

    def test_stop_method(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        listener = Listener(executor=executor)

        with self.long_running_task(executor):
            self.assertEqual(executor.state, RUNNING)
            executor.stop()
            self.assertEqual(executor.state, STOPPING)

        self.waitForStop(executor)
        self.assertEqual(executor.state, STOPPED)
        self.assertEqual(listener.states, [RUNNING, STOPPING, STOPPED])

    def test_stop_method_with_no_jobs(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        listener = Listener(executor=executor)

        self.assertEqual(executor.state, RUNNING)
        executor.stop()
        self.waitForStop(executor)
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

        self.waitForStop(executor)
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

        self.waitForStop(executor)
        self.assertEqual(executor.state, STOPPED)
        with self.assertRaises(RuntimeError):
            executor.submit_call(int)

    def test_stop_cancels_running_futures(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        with self.long_running_task(executor) as future:
            self.waitUntilExecuting(future)

            self.assertEqual(future.state, EXECUTING)
            executor.stop()
            self.assertEqual(future.state, CANCELLING)

        self.waitForFuture(future)
        self.assertEqual(future.state, CANCELLED)

    # Helper methods and assertions ###########################################

    def waitForStop(self, executor):
        """"
        Wait for the executor to reach STOPPED state.
        """
        def executor_stopped():
            return executor.state == STOPPED

        with self.event_loop_until_condition(executor_stopped):
            pass

    def waitUntilExecuting(self, future):
        """
        Wait until the given future is executing.
        """
        def future_executing():
            return future.state == EXECUTING

        with self.event_loop_until_condition(future_executing):
            pass

    def waitForFuture(self, future):
        """
        Wait until the given future completes.
        """
        with self.event_loop_until_condition(lambda: future.done):
            pass

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
