# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Common tests for TraitsExecutor behaviour. These will be exercised
in different contexts.
"""

import contextlib

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
    ExecutorState,
    RUNNING,
    STOPPED,
    STOPPING,
    submit_call,
    TraitsExecutor,
)


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


class TraitsExecutorTests:
    def test_stop_method(self):
        with self.long_running_task(self.executor):
            self.assertEqual(self.executor.state, RUNNING)
            self.executor.stop()
            self.assertEqual(self.executor.state, STOPPING)

        self.wait_until_stopped(self.executor)
        self.assertEqual(self.executor.state, STOPPED)
        self.assertEqual(self.listener.states, [RUNNING, STOPPING, STOPPED])

    def test_stop_method_with_no_jobs(self):
        self.assertEqual(self.executor.state, RUNNING)
        self.executor.stop()
        self.wait_until_stopped(self.executor)
        self.assertEqual(self.executor.state, STOPPED)
        self.assertEqual(self.listener.states, [RUNNING, STOPPING, STOPPED])

    def test_stop_method_raises_unless_running(self):
        with self.long_running_task(self.executor):
            self.assertEqual(self.executor.state, RUNNING)
            self.executor.stop()

            # Raises if in STOPPING mode.
            self.assertEqual(self.executor.state, STOPPING)
            with self.assertRaises(RuntimeError):
                self.executor.stop()

        self.wait_until_stopped(self.executor)
        # Raises if in STOPPED mode.
        self.assertEqual(self.executor.state, STOPPED)
        with self.assertRaises(RuntimeError):
            self.executor.stop()

    def test_cant_submit_new_unless_running(self):
        with self.long_running_task(self.executor):
            self.executor.stop()
            self.assertEqual(self.executor.state, STOPPING)

            with self.assertRaises(RuntimeError):
                submit_call(self.executor, len, (1, 2, 3))

        self.wait_until_stopped(self.executor)
        self.assertEqual(self.executor.state, STOPPED)
        with self.assertRaises(RuntimeError):
            submit_call(self.executor, int)

    def test_stop_cancels_running_futures(self):
        with self.long_running_task(self.executor) as future:
            self.wait_for_state(future, EXECUTING)

            self.assertEqual(future.state, EXECUTING)
            self.executor.stop()
            self.assertEqual(future.state, CANCELLING)

        self.wait_until_done(future)
        self.assertEqual(future.state, CANCELLED)

        self.wait_until_stopped(self.executor)
        self.assertEqual(self.executor.state, STOPPED)

    def test_running(self):
        self.assertTrue(self.executor.running)

        with self.long_running_task(self.executor):
            self.assertTrue(self.executor.running)
            self.executor.stop()
            self.assertFalse(self.executor.running)

        self.wait_until_stopped(self.executor)
        self.assertFalse(self.executor.running)

    def test_stopped(self):
        self.assertFalse(self.executor.stopped)

        with self.long_running_task(self.executor):
            self.assertFalse(self.executor.stopped)
            self.executor.stop()
            self.assertFalse(self.executor.stopped)

        self.wait_until_stopped(self.executor)
        self.assertTrue(self.executor.stopped)

    def test_submit_call_method(self):
        with self.assertWarns(DeprecationWarning) as warning_info:
            future = self.executor.submit_call(
                test_call, "arg1", "arg2", kwd1="kwd1", kwd2="kwd2"
            )

        self.wait_until_done(future)

        self.assertEqual(
            future.result,
            (("arg1", "arg2"), {"kwd1": "kwd1", "kwd2": "kwd2"}),
        )

        _, _, this_module = __name__.rpartition(".")
        self.assertIn(this_module, warning_info.filename)
        self.assertIn(
            "submit_call method is deprecated",
            str(warning_info.warning),
        )

    def test_submit_iteration_method(self):
        with self.assertWarns(DeprecationWarning) as warning_info:
            future = self.executor.submit_iteration(
                test_iteration,
                "arg1",
                "arg2",
                kwd1="kwd1",
                kwd2="kwd2",
            )

        results = []
        future.on_trait_change(
            lambda result: results.append(result), "result_event"
        )

        self.wait_until_done(future)
        self.assertEqual(
            results,
            [("arg1", "arg2"), {"kwd1": "kwd1", "kwd2": "kwd2"}],
        )

        _, _, this_module = __name__.rpartition(".")
        self.assertIn(this_module, warning_info.filename)
        self.assertIn(
            "submit_iteration method is deprecated",
            str(warning_info.warning),
        )

    def test_submit_progress_method(self):
        with self.assertWarns(DeprecationWarning) as warning_info:
            future = self.executor.submit_progress(
                test_progress,
                "arg1",
                "arg2",
                kwd1="kwd1",
                kwd2="kwd2",
            )

        self.wait_until_done(future)

        self.assertEqual(
            future.result,
            ("arg1", "arg2", "kwd1", "kwd2"),
        )

        _, _, this_module = __name__.rpartition(".")
        self.assertIn(this_module, warning_info.filename)
        self.assertIn(
            "submit_progress method is deprecated",
            str(warning_info.warning),
        )

    def test_states_consistent(self):
        # Triples (state, running, stopped).
        states = []

        def record_states():
            states.append(
                (
                    self.executor.state,
                    self.executor.running,
                    self.executor.stopped,
                )
            )

        self.executor.on_trait_change(record_states, "running")
        self.executor.on_trait_change(record_states, "stopped")
        self.executor.on_trait_change(record_states, "state")
        submit_call(self.executor, int)

        # Record states before, during, and after stopping.
        record_states()
        self.executor.stop()
        self.wait_until_stopped(self.executor)
        record_states()

        for state, running, stopped in states:
            self.assertEqual(running, state == RUNNING)
            self.assertEqual(stopped, state == STOPPED)

    def test_running_and_stopped_fired_only_once(self):
        submit_call(self.executor, int)
        self.executor.stop()
        self.wait_until_stopped(self.executor)

        self.assertEqual(self.listener.running_changes, [(True, False)])
        self.assertEqual(self.listener.stopped_changes, [(False, True)])

    def test_running_and_stopped_fired_only_once_no_futures(self):
        # Same as above but tests the case where the executor goes to STOPPED
        # state the moment that stop is called.
        self.executor.stop()
        self.wait_until_stopped(self.executor)

        self.assertEqual(self.listener.running_changes, [(True, False)])
        self.assertEqual(self.listener.stopped_changes, [(False, True)])

    def test_multiple_futures(self):
        futures = []
        for i in range(100):
            futures.append(submit_call(self.executor, str, i))

        listener = FuturesListener(futures=futures)

        # Wait for all futures to complete.
        self.run_until(
            listener, "all_done", lambda listener: listener.all_done
        )

        for i, future in enumerate(futures):
            self.assertEqual(future.result, str(i))

    def test_stop_with_multiple_futures(self):
        futures = []
        for i in range(100):
            futures.append(submit_call(self.executor, str, i))

        self.executor.stop()
        self.wait_until_stopped(self.executor)

        for future in futures:
            self.assertEqual(future.state, CANCELLED)

    # Helper methods and assertions ###########################################

    def wait_until_stopped(self, executor):
        """
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
        event = self._context.event()
        try:
            yield submit_call(executor, event.wait)
        finally:
            event.set()
