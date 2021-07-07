# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
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
import queue
import threading
import time

from traits.api import (
    Bool,
    HasStrictTraits,
    Instance,
    List,
    observe,
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

#: Maximum timeout for blocking calls, in seconds. A successful test should
#: never hit this timeout - it's there to prevent a failing test from hanging
#: forever and blocking the rest of the test suite.
SAFETY_TIMEOUT = 5.0


def test_call(*args, **kwds):
    """Simple test target for submit_call."""
    return args, kwds


def test_iteration(*args, **kwargs):
    """Simple test target for submit_iteration."""
    yield args
    yield kwargs


def test_progress(arg1, arg2, kwd1, kwd2, progress):
    """Simple test target for submit_progress."""
    return arg1, arg2, kwd1, kwd2


def slow_call(starting, stopping):
    """Target background task used to check waiting behaviour of 'shutdown'.

    Parameters
    ----------
    starting, stopping : threading.Event
    """
    starting.set()
    time.sleep(0.1)
    stopping.set()


def wait_for_event(started, event, timeout):
    """Wait for an event, and raise if it doesn't occur within a timeout.

    Also signals via an event when it starts executing.

    Parameters
    ----------
    started : threading.Event
        Event set when this function starts executing.
    event : threading.Event
        Event to wait for.
    timeout : float
        Maximum time to wait, in seconds.

    Raises
    ------
    RuntimeError
        If the event remains unset after the given timeout.
    """
    started.set()
    if not event.wait(timeout=timeout):
        raise RuntimeError("Timed out waiting for event")


class ExecutorListener(HasStrictTraits):
    """Listener for executor state changes."""

    #: Executor that we're listening to.
    executor = Instance(TraitsExecutor)

    #: List of states of that executor.
    states = List(ExecutorState)

    #: Changes to the 'running' trait value.
    running_changes = List(Tuple(Bool(), Bool()))

    #: Changes to the 'stopped' trait value.
    stopped_changes = List(Tuple(Bool(), Bool()))

    @observe("executor:state")
    def _record_state_change(self, event):
        old_state, new_state = event.old, event.new
        if not self.states:
            # On the first state change, record the initial state as well as
            # the new one.
            self.states.append(old_state)
        self.states.append(new_state)

    @observe("executor:running")
    def _record_running_change(self, event):
        old, new = event.old, event.new
        self.running_changes.append((old, new))

    @observe("executor:stopped")
    def _record_stopped_change(self, event):
        old, new = event.old, event.new
        self.stopped_changes.append((old, new))


class FuturesListener(HasStrictTraits):
    """
    Listener for multiple futures.
    """

    #: List of futures that we're listening to.
    futures = List(Instance(CallFuture))

    #: True when all futures have completed.
    all_done = Property(Bool(), observe="futures:items:done")

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

    def test_shutdown_when_already_stopping(self):
        with self.long_running_task(self.executor):
            self.assertEqual(self.executor.state, RUNNING)
            self.executor.stop()

        self.assertEqual(self.executor.state, STOPPING)
        self.executor.shutdown(timeout=SAFETY_TIMEOUT)
        self.assertEqual(self.executor.state, STOPPED)

    def test_shutdown_does_nothing_if_stopped(self):
        self.assertEqual(self.executor.state, RUNNING)
        self.executor.stop()
        self.wait_until_stopped(self.executor)
        self.assertEqual(self.executor.state, STOPPED)
        self.executor.shutdown(timeout=SAFETY_TIMEOUT)
        self.assertEqual(self.executor.state, STOPPED)

    def test_shutdown_cancels_running_futures(self):
        future = submit_call(self.executor, pow, 3, 5)
        self.executor.shutdown(timeout=SAFETY_TIMEOUT)
        self.assertEqual(future.state, CANCELLING)
        self.assertTrue(self.executor.stopped)

    def test_no_future_updates_after_shutdown(self):
        future = submit_call(self.executor, pow, 3, 5)
        self.executor.shutdown(timeout=SAFETY_TIMEOUT)
        self.assertEqual(future.state, CANCELLING)
        self.exercise_event_loop()
        self.assertEqual(future.state, CANCELLING)

    def test_shutdown_goes_through_stopping_state(self):
        self.executor.shutdown(timeout=SAFETY_TIMEOUT)
        self.assertEqual(
            self.listener.states,
            [RUNNING, STOPPING, STOPPED],
        )

    def test_shutdown_waits_for_background_tasks(self):
        starting = self._context.event()
        stopping = self._context.event()
        submit_call(self.executor, slow_call, starting, stopping)

        # Make sure background task has started, else it might be
        # cancelled altogether.
        self.assertTrue(starting.wait(timeout=SAFETY_TIMEOUT))

        self.executor.shutdown(timeout=SAFETY_TIMEOUT)
        self.assertTrue(stopping.is_set())

    def test_shutdown_timeout(self):
        start_time = time.monotonic()
        with self.long_running_task(self.executor):
            with self.assertRaises(RuntimeError):
                self.executor.shutdown(timeout=0.1)

        actual_timeout = time.monotonic() - start_time
        self.assertLess(actual_timeout, 1.0)
        self.assertEqual(self.executor.state, STOPPING)

        self.executor.shutdown(timeout=SAFETY_TIMEOUT)
        self.assertEqual(self.executor.state, STOPPED)

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
        future.observe(lambda event: results.append(event.new), "result_event")

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

        def record_states(event=None):
            states.append(
                (
                    self.executor.state,
                    self.executor.running,
                    self.executor.stopped,
                )
            )

        self.executor.observe(record_states, "running")
        self.executor.observe(record_states, "stopped")
        self.executor.observe(record_states, "state")
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

    def test_submit_from_background_thread(self):
        def target(executor, msg_queue):
            """
            Submit a simple callable to the given executor, and report
            the result of that submission to a queue.
            """
            try:
                future = submit_call(executor, pow, 2, 3)
            except BaseException as exc:
                msg_queue.put(("FAILED", exc))
            else:
                msg_queue.put(("DONE", future))

        msg_queue = queue.Queue()
        worker = threading.Thread(
            target=target, args=(self.executor, msg_queue)
        )
        worker.start()
        try:
            result_type, future_or_exc = msg_queue.get(timeout=SAFETY_TIMEOUT)
        finally:
            worker.join(timeout=SAFETY_TIMEOUT)

        self.assertEqual(result_type, "FAILED")
        self.assertIsInstance(future_or_exc, RuntimeError)

    # Helper methods and assertions ###########################################

    def exercise_event_loop(self):
        """
        Exercise the event loop.

        Places a new task on the event loop and runs the event loop
        until that task is complete. The goal is to flush out any other
        tasks that might already be in event loop tasks queue.
        """

        class Sentinel(HasStrictTraits):
            #: Simple boolean flag.
            flag = Bool(False)

        sentinel = Sentinel()

        self._event_loop_helper.setattr_soon(sentinel, "flag", True)
        self.run_until(sentinel, "flag", lambda sentinel: sentinel.flag)

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
    def long_running_task(self, executor, timeout=SAFETY_TIMEOUT):
        """
        Simulate a long-running task being submitted to the executor.

        This context manager waits for the task to start executing before
        yielding the future associated to that task. The task will be
        terminated either at timeout or on exit of the associated with block.
        """
        started = self._context.event()
        event = self._context.event()
        try:
            future = submit_call(
                executor, wait_for_event, started, event, timeout
            )
            self.assertTrue(started.wait(timeout=timeout))
            yield future
        finally:
            event.set()
