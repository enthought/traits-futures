# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Tests for the TraitsExecutor class.
"""
from __future__ import absolute_import, print_function, unicode_literals

import concurrent.futures
import contextlib
import threading
import unittest

from pyface.ui.qt4.util.gui_test_assistant import GuiTestAssistant
from traits.api import (
    Bool, HasStrictTraits, Instance, List, on_trait_change, Tuple)

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


class ExecutorListener(HasStrictTraits):
    """ Listener for executor state changes. """
    #: Executor that we're listening to.
    executor = Instance(TraitsExecutor)

    #: List of states of that executor.
    states = List(ExecutorState)

    #: Changes to the 'running' trait value.
    running_changes = List(Tuple(Bool(), Bool()))

    #: Changes to the 'stopped' trait value.
    stopped_changes = List(Tuple(Bool(), Bool()))

    @on_trait_change('executor:state')
    def _record_state_change(self, obj, name, old_state, new_state):
        if not self.states:
            # On the first state change, record the initial state as well as
            # the new one.
            self.states.append(old_state)
        self.states.append(new_state)

    @on_trait_change('executor:running')
    def _record_running_change(self, object, name, old, new):
        self.running_changes.append((old, new))

    @on_trait_change('executor:stopped')
    def _record_stopped_change(self, object, name, old, new):
        self.stopped_changes.append((old, new))


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
        listener = ExecutorListener(executor=executor)

        with self.long_running_task(executor):
            self.assertEqual(executor.state, RUNNING)
            executor.stop()
            self.assertEqual(executor.state, STOPPING)

        self.wait_for_stop(executor)
        self.assertEqual(executor.state, STOPPED)
        self.assertEqual(listener.states, [RUNNING, STOPPING, STOPPED])

    def test_stop_method_with_no_jobs(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        listener = ExecutorListener(executor=executor)

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

        # Careful: this is a concurrent.futures Future instance, not
        # one of our traits_futures Futures.
        cf_future = self.thread_pool.submit(int)
        self.assertEqual(cf_future.result(), 0)

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
        future.on_trait_change(
            lambda result: results.append(result), 'result_event')

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

    def test_states_consistent(self):
        # Triples (state, running, stopped).
        states = []

        def record_states():
            states.append((executor.state, executor.running, executor.stopped))

        executor = TraitsExecutor(thread_pool=self.thread_pool)
        executor.on_trait_change(record_states, 'running')
        executor.on_trait_change(record_states, 'stopped')
        executor.on_trait_change(record_states, 'state')
        executor.submit_call(int)

        # Record states before, during, and after stopping.
        record_states()
        executor.stop()
        self.wait_for_stop(executor)
        record_states()

        for state, running, stopped in states:
            self.assertEqual(running, state == RUNNING)
            self.assertEqual(stopped, state == STOPPED)

    def test_running_and_stopped_fired_only_once(self):
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        listener = ExecutorListener(executor=executor)

        executor.submit_call(int)
        executor.stop()
        self.wait_for_stop(executor)

        self.assertEqual(listener.running_changes, [(True, False)])
        self.assertEqual(listener.stopped_changes, [(False, True)])

    def test_running_and_stopped_fired_only_once_no_futures(self):
        # Same as above but tests the case where the executor goes to STOPPED
        # state the moment that stop is called.
        executor = TraitsExecutor(thread_pool=self.thread_pool)
        listener = ExecutorListener(executor=executor)

        executor.stop()
        self.wait_for_stop(executor)

        self.assertEqual(listener.running_changes, [(True, False)])
        self.assertEqual(listener.stopped_changes, [(False, True)])

    # Helper methods and assertions ###########################################

    def wait_for_stop(self, executor):
        """"
        Wait for the executor to reach STOPPED state.
        """
        with self.event_loop_until_condition(lambda: executor.stopped):
            pass

    def wait_until_executing(self, future):
        """
        Wait until the given future is executing.
        """
        def future_executing():
            return future.state == EXECUTING

        with self.event_loop_until_condition(future_executing):
            pass

    def wait_for_future(self, future):
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
