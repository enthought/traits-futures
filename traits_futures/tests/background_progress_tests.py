# (C) Copyright 2018-2023 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

from traits.api import Any, HasStrictTraits, Instance, List, observe

from traits_futures.api import (
    CANCELLED,
    CANCELLING,
    COMPLETED,
    EXECUTING,
    FAILED,
    FutureState,
    ProgressFuture,
    submit_progress,
    TaskCancelled,
    WAITING,
)

#: Timeout for blocking operations, in seconds.
TIMEOUT = 10.0


# Target functions used for testing ###########################################


def progress_reporting_sum(numbers, progress):
    """
    Sum a list of numbers, reporting progress at each step.
    """
    count = len(numbers)

    total = 0
    for i, number in enumerate(numbers):
        progress((i, count))
        total += number
    progress((count, count))
    return total


def bad_progress_reporting_function(progress):
    """
    Target function that raises an exception.
    """
    progress((5, 10))
    1 / 0


def wait_then_fail(signal, progress):
    """
    Target function that waits until given permission to proceed, then fails.
    """
    signal.wait(timeout=TIMEOUT)
    1 / 0


def progress_then_signal(signal, progress):
    """
    Target function that emits progress, then signals.
    """
    progress(1)
    progress(2)
    signal.set()


def syncing_progress(test_ready, raised, progress):
    """
    Target function that allows synchronization with the main thread between
    the first and second progress notifications.
    """
    progress("first")
    # Synchronise with the test.
    test_ready.wait(timeout=TIMEOUT)
    # After the test cancels, the second progress send operation should raise,
    # so that we never get to the following code.
    try:
        progress("second")
    except TaskCancelled:
        raised.set()
        raise


def event_set_with_progress(event, progress):
    """
    Target function that simply sets an event.
    """
    event.set()


def resource_acquirer(acquired, ready, checkpoint, progress):
    """
    Target function that acquires a resource.
    """
    acquired.set()
    try:
        checkpoint.set()
        ready.wait(timeout=TIMEOUT)
    finally:
        acquired.clear()


class ProgressFutureListener(HasStrictTraits):
    """
    Listener for a ProgressFuture. Records state changes and progress messages.
    """

    #: Future that we're listening to.
    future = Instance(ProgressFuture)

    #: List of states of that future.
    states = List(FutureState)

    #: List of progress messages received.
    progress = List(Any())

    @observe("future:state")
    def record_state_change(self, event):
        old_state, new_state = event.old, event.new
        if not self.states:
            # On the first state change, record the initial state as well as
            # the new one.
            self.states.append(old_state)
        self.states.append(new_state)

    @observe("future:progress")
    def record_progress(self, event):
        progress_info = event.new
        self.progress.append(progress_info)


class BackgroundProgressTests:
    def test_progress(self):
        # Straightforward case.
        future = submit_progress(
            self.executor, progress_reporting_sum, [1, 2, 3]
        )
        listener = ProgressFutureListener(future=future)

        self.wait_until_done(future)

        self.assertResult(future, 6)
        self.assertNoException(future)
        self.assertEqual(listener.states, [WAITING, EXECUTING, COMPLETED])

        expected_progress = [(0, 3), (1, 3), (2, 3), (3, 3)]
        self.assertEqual(listener.progress, expected_progress)

    def test_progress_with_progress_keyword_argument(self):
        with self.assertRaises(TypeError):
            submit_progress(
                self.executor, progress_reporting_sum, [1, 2, 3], progress=None
            )

    def test_failed_progress(self):
        # Callable that raises.
        future = submit_progress(
            self.executor, bad_progress_reporting_function
        )
        listener = ProgressFutureListener(future=future)

        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertException(future, ZeroDivisionError)
        self.assertEqual(listener.states, [WAITING, EXECUTING, FAILED])

        expected_progress = [(5, 10)]
        self.assertEqual(listener.progress, expected_progress)

    def test_cancellation_before_execution(self):
        event = self._context.event()

        future = submit_progress(self.executor, event_set_with_progress, event)
        listener = ProgressFutureListener(future=future)

        self.assertTrue(event.wait(timeout=TIMEOUT))
        self.assertTrue(future.cancellable)
        future.cancel()
        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_background_task_starts(self):
        # Test case where the background task is cancelled before
        # it even starts executing.
        event = self._context.event()

        with self.block_worker_pool():
            future = submit_progress(
                self.executor, event_set_with_progress, event
            )
            listener = ProgressFutureListener(future=future)
            future.cancel()

        self.wait_until_done(future)

        self.assertFalse(event.is_set())

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(listener.states, [WAITING, CANCELLING, CANCELLED])

    def test_progress_allows_cancellation(self):
        test_ready = self._context.event()
        raised = self._context.event()

        future = submit_progress(
            self.executor, syncing_progress, test_ready, raised
        )
        listener = ProgressFutureListener(future=future)

        # Wait until we get the first progress message.
        self.run_until(
            listener,
            "progress_items",
            lambda listener: len(listener.progress) > 0,
        )

        # Cancel, then allow the background task to continue.
        future.cancel()
        test_ready.set()

        self.wait_until_done(future)

        self.assertTrue(raised.is_set())
        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states, [WAITING, EXECUTING, CANCELLING, CANCELLED]
        )
        self.assertEqual(listener.progress, ["first"])

    def test_double_cancellation(self):
        future = submit_progress(self.executor, progress_reporting_sum, [1, 2])
        self.assertTrue(future.cancellable)
        future.cancel()

        self.assertFalse(future.cancellable)
        cancelled = future.cancel()
        self.assertFalse(cancelled)

    def test_cancel_raising_task(self):
        signal = self._context.event()
        future = submit_progress(self.executor, wait_then_fail, signal)

        self.wait_for_state(future, EXECUTING)

        future.cancel()
        signal.set()

        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)

    def test_progress_messages_after_cancellation(self):
        signal = self._context.event()
        future = submit_progress(self.executor, progress_then_signal, signal)
        listener = ProgressFutureListener(future=future)

        # Let the background task run to completion; it will have already sent
        # progress messages.
        self.assertTrue(signal.wait(timeout=TIMEOUT))

        future.cancel()

        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(listener.states, [WAITING, CANCELLING, CANCELLED])
        self.assertEqual(listener.progress, [])

    def test_progress_cleanup_on_cancellation(self):
        acquired = self._context.event()
        ready = self._context.event()
        checkpoint = self._context.event()

        try:
            future = submit_progress(
                self.executor, resource_acquirer, acquired, ready, checkpoint
            )

            self.wait_for_state(future, EXECUTING)
            self.assertTrue(checkpoint.wait(timeout=TIMEOUT))
            self.assertTrue(acquired.is_set())
            future.cancel()
        finally:
            ready.set()

        self.wait_until_done(future)
        self.assertFalse(acquired.is_set())

    # Helper functions

    def halt_executor(self):
        """
        Wait for the executor to stop.
        """
        executor = self.executor
        executor.shutdown(timeout=TIMEOUT)
        del self.executor

    def wait_until_done(self, future):
        self.run_until(future, "done", lambda future: future.done)

    def wait_for_state(self, future, state):
        self.run_until(future, "state", lambda future: future.state == state)

    # Assertions

    def assertResult(self, future, expected_result):
        self.assertEqual(future.result, expected_result)

    def assertNoResult(self, future):
        with self.assertRaises(AttributeError):
            future.result

    def assertNoException(self, future):
        with self.assertRaises(AttributeError):
            future.exception

    def assertException(self, future, exc_type):
        self.assertIn(exc_type.__name__, future.exception[0])
