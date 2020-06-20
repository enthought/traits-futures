# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Tests for the TraitsExecutor class.
"""
import concurrent.futures
import contextlib
import threading
import unittest

from traits.api import (
    Bool,
    HasStrictTraits,
    Instance,
    List,
    on_trait_change,
    Property,
    Tuple,
)

from traits_futures.api import (
    CallFuture,
    CANCELLED,
    CANCELLING,
    EXECUTING,
    TraitsExecutor,
    ExecutorState,
    RUNNING,
    STOPPING,
    STOPPED,
)
from traits_futures.toolkit_support import toolkit

GuiTestAssistant = toolkit("gui_test_assistant:GuiTestAssistant")


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

    @on_trait_change("executor:state")
    def _record_state_change(self, obj, name, old_state, new_state):
        if not self.states:
            # On the first state change, record the initial state as well as
            # the new one.
            self.states.append(old_state)
        self.states.append(new_state)

    @on_trait_change("executor:running")
    def _record_running_change(self, object, name, old, new):
        self.running_changes.append((old, new))

    @on_trait_change("executor:stopped")
    def _record_stopped_change(self, object, name, old, new):
        self.stopped_changes.append((old, new))


class FuturesListener(HasStrictTraits):
    """
    Listener for multiple futures.
    """

    #: List of futures that we're listening to.
    futures = List(Instance(CallFuture))

    #: True when all futures have completed.
    all_done = Property(Bool(), depends_on="futures:done")

    def _get_all_done(self):
        return all(future.done for future in self.futures)


def test_call(*args, **kwds):
    """ Simple test target for submit_call. """
    return args, kwds


def test_iteration(*args, **kwargs):
    """ Simple test target for submit_iteration. """
    yield args
    yield kwargs


def test_progress(arg1, arg2, kwd1, kwd2, progress):
    """ Simple test target for submit_progress. """
    return arg1, arg2, kwd1, kwd2


class TestTraitsExecutor(GuiTestAssistant, unittest.TestCase):
    def setUp(self):
        GuiTestAssistant.setUp(self)

    def tearDown(self):
        if hasattr(self, "executor"):
            self.executor.stop()
            self.wait_until_stopped(self.executor)
            del self.executor
        GuiTestAssistant.tearDown(self)

    def test_max_workers(self):
        executor = TraitsExecutor(max_workers=11)
        self.assertEqual(executor._thread_pool._max_workers, 11)
        executor.stop()
        self.wait_until_stopped(executor)

    def test_max_workers_mutually_exclusive_with_thread_pool(self):
        with self.temporary_thread_pool() as thread_pool:
            with self.assertRaises(TypeError):
                TraitsExecutor(worker_pool=thread_pool, max_workers=11)

    def test_stop_method(self):
        executor = TraitsExecutor()
        listener = ExecutorListener(executor=executor)

        with self.long_running_task(executor):
            self.assertEqual(executor.state, RUNNING)
            executor.stop()
            self.assertEqual(executor.state, STOPPING)

        self.wait_until_stopped(executor)
        self.assertEqual(executor.state, STOPPED)
        self.assertEqual(listener.states, [RUNNING, STOPPING, STOPPED])

    def test_stop_method_with_no_jobs(self):
        executor = TraitsExecutor()
        listener = ExecutorListener(executor=executor)

        self.assertEqual(executor.state, RUNNING)
        executor.stop()
        self.wait_until_stopped(executor)
        self.assertEqual(executor.state, STOPPED)
        self.assertEqual(listener.states, [RUNNING, STOPPING, STOPPED])

    def test_stop_method_raises_unless_running(self):
        executor = TraitsExecutor()

        with self.long_running_task(executor):
            self.assertEqual(executor.state, RUNNING)
            executor.stop()

            # Raises if in STOPPING mode.
            self.assertEqual(executor.state, STOPPING)
            with self.assertRaises(RuntimeError):
                executor.stop()

        self.wait_until_stopped(executor)
        # Raises if in STOPPED mode.
        self.assertEqual(executor.state, STOPPED)
        with self.assertRaises(RuntimeError):
            executor.stop()

    def test_cant_submit_new_unless_running(self):
        executor = TraitsExecutor()
        with self.long_running_task(executor):
            executor.stop()
            self.assertEqual(executor.state, STOPPING)

            with self.assertRaises(RuntimeError):
                executor.submit_call(len, (1, 2, 3))

        self.wait_until_stopped(executor)
        self.assertEqual(executor.state, STOPPED)
        with self.assertRaises(RuntimeError):
            executor.submit_call(int)

    def test_stop_cancels_running_futures(self):
        executor = TraitsExecutor()
        with self.long_running_task(executor) as future:
            self.wait_for_state(future, EXECUTING)

            self.assertEqual(future.state, EXECUTING)
            executor.stop()
            self.assertEqual(future.state, CANCELLING)

        self.wait_until_done(future)
        self.assertEqual(future.state, CANCELLED)

        self.wait_until_stopped(executor)
        self.assertEqual(executor.state, STOPPED)

    def test_running(self):
        executor = TraitsExecutor()
        self.assertTrue(executor.running)

        with self.long_running_task(executor):
            self.assertTrue(executor.running)
            executor.stop()
            self.assertFalse(executor.running)

        self.wait_until_stopped(executor)
        self.assertFalse(executor.running)

    def test_stopped(self):
        executor = TraitsExecutor()
        self.assertFalse(executor.stopped)

        with self.long_running_task(executor):
            self.assertFalse(executor.stopped)
            executor.stop()
            self.assertFalse(executor.stopped)

        self.wait_until_stopped(executor)
        self.assertTrue(executor.stopped)

    def test_owned_thread_pool(self):
        executor = TraitsExecutor()
        thread_pool = executor._thread_pool

        executor.stop()
        self.wait_until_stopped(executor)

        # Check that the internally-created thread pool has been shut down.
        with self.assertRaises(RuntimeError):
            thread_pool.submit(int)

    def test_thread_pool_argument_deprecated(self):
        with self.temporary_thread_pool() as thread_pool:
            with self.assertWarns(DeprecationWarning) as warning_info:
                executor = TraitsExecutor(thread_pool=thread_pool)
            executor.stop()
            self.wait_until_stopped(executor)

        # Check we're using the right stack level in the warning.
        *_, this_module = __name__.rsplit(".")
        self.assertIn(this_module, warning_info.filename)

    def test_shared_thread_pool(self):
        with self.temporary_thread_pool() as thread_pool:
            executor = TraitsExecutor(worker_pool=thread_pool)
            executor.stop()
            self.wait_until_stopped(executor)

            # Check that the the shared thread pool is still usable.
            cf_future = thread_pool.submit(int)
            self.assertEqual(cf_future.result(), 0)

    def test_submit_call(self):
        self.executor = TraitsExecutor()
        future = self.executor.submit_call(
            test_call, "arg1", "arg2", kwd1="kwd1", kwd2="kwd2"
        )

        self.wait_until_done(future)

        self.assertEqual(
            future.result,
            (("arg1", "arg2"), {"kwd1": "kwd1", "kwd2": "kwd2"}),
        )

    def test_submit_iteration(self):
        self.executor = TraitsExecutor()
        future = self.executor.submit_iteration(
            test_iteration, "arg1", "arg2", kwd1="kwd1", kwd2="kwd2"
        )

        results = []
        future.on_trait_change(
            lambda result: results.append(result), "result_event"
        )

        self.wait_until_done(future)
        self.assertEqual(
            results, [("arg1", "arg2"), {"kwd1": "kwd1", "kwd2": "kwd2"}],
        )

    def test_submit_progress(self):
        self.executor = TraitsExecutor()
        future = self.executor.submit_progress(
            test_progress, "arg1", "arg2", kwd1="kwd1", kwd2="kwd2"
        )

        self.wait_until_done(future)

        self.assertEqual(
            future.result, ("arg1", "arg2", "kwd1", "kwd2"),
        )

    def test_states_consistent(self):
        # Triples (state, running, stopped).
        states = []

        def record_states():
            states.append((executor.state, executor.running, executor.stopped))

        executor = TraitsExecutor()
        executor.on_trait_change(record_states, "running")
        executor.on_trait_change(record_states, "stopped")
        executor.on_trait_change(record_states, "state")
        executor.submit_call(int)

        # Record states before, during, and after stopping.
        record_states()
        executor.stop()
        self.wait_until_stopped(executor)
        record_states()

        for state, running, stopped in states:
            self.assertEqual(running, state == RUNNING)
            self.assertEqual(stopped, state == STOPPED)

    def test_running_and_stopped_fired_only_once(self):
        executor = TraitsExecutor()
        listener = ExecutorListener(executor=executor)

        executor.submit_call(int)
        executor.stop()
        self.wait_until_stopped(executor)

        self.assertEqual(listener.running_changes, [(True, False)])
        self.assertEqual(listener.stopped_changes, [(False, True)])

    def test_running_and_stopped_fired_only_once_no_futures(self):
        # Same as above but tests the case where the executor goes to STOPPED
        # state the moment that stop is called.
        executor = TraitsExecutor()
        listener = ExecutorListener(executor=executor)

        executor.stop()
        self.wait_until_stopped(executor)

        self.assertEqual(listener.running_changes, [(True, False)])
        self.assertEqual(listener.stopped_changes, [(False, True)])

    def test_multiple_futures(self):
        self.executor = TraitsExecutor()

        futures = []
        for i in range(100):
            futures.append(self.executor.submit_call(str, i))

        listener = FuturesListener(futures=futures)

        # Wait for all futures to complete.
        self.run_until(
            listener, "all_done", lambda listener: listener.all_done
        )

        for i, future in enumerate(futures):
            self.assertEqual(future.result, str(i))

    def test_stop_with_multiple_futures(self):
        executor = TraitsExecutor()

        futures = []
        for i in range(100):
            futures.append(executor.submit_call(str, i))

        executor.stop()
        self.wait_until_stopped(executor)

        for future in futures:
            self.assertEqual(future.state, CANCELLED)

    # Helper methods and assertions ###########################################

    def wait_until_stopped(self, executor):
        """"
        Wait for the executor to reach STOPPED state.
        """
        self.run_until(executor, "stopped", lambda executor: executor.stopped)

    def wait_until_done(self, future):
        self.run_until(future, "done", lambda future: future.done)

    def wait_for_state(self, future, state):
        self.run_until(future, "state", lambda future: future.state == state)

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

    @contextlib.contextmanager
    def temporary_thread_pool(self):
        """
        Create a thread pool that's shut down at the end of the with block.
        """
        thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        try:
            yield thread_pool
        finally:
            thread_pool.shutdown()
