"""
Tests for the TraitsExecutor class.
"""
import concurrent.futures
import contextlib
import threading
import unittest

from pyface.ui.qt4.util.gui_test_assistant import GuiTestAssistant
from traits.api import HasStrictTraits, Instance, List, on_trait_change

from traits_futures.api import (
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

    def test_initial_state(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        self.assertEqual(executor.state, RUNNING)

    def test_stop_method(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        listener = Listener(executor=executor)

        event = threading.Event()
        executor.submit_call(event.wait)

        self.assertEqual(executor.state, RUNNING)
        executor.stop()
        self.assertEqual(executor.state, STOPPING)

        event.set()

        self.assertEventuallyStops(executor)
        self.assertEqual(listener.states, [RUNNING, STOPPING, STOPPED])

    def test_stop_method_with_no_jobs(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        listener = Listener(executor=executor)

        executor.stop()

        self.assertEventuallyStops(executor)
        self.assertEqual(listener.states, [RUNNING, STOPPING, STOPPED])

    def test_stop_method_raises_unless_running(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        listener = Listener(executor=executor)

        with self.long_running_task(executor):
            self.assertEqual(executor.state, RUNNING)
            executor.stop()
            # Raises if in STOPPING mode.
            self.assertEqual(executor.state, STOPPING)
            with self.assertRaises(RuntimeError):
                executor.stop()

        self.assertEventuallyStops(executor)
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

        self.assertEventuallyStops(executor)
        self.assertEqual(executor.state, STOPPED)
        with self.assertRaises(RuntimeError):
            executor.submit_call(int)

    # Helper methods and assertions ###########################################

    def assertEventuallyStops(self, executor):
        """"
        Assert that the given executor eventually reaches STOPPED state.
        """
        def executor_stopped():
            return executor.state == STOPPED

        with self.event_loop_until_condition(executor_stopped):
            pass

    @contextlib.contextmanager
    def long_running_task(self, executor):
        """
        Simulate a long-running task being submitted to the executor.

        The task finishes on exit of the with block.
        """
        event = threading.Event()
        try:
            executor.submit_call(event.wait)
            yield
        finally:
            event.set()
