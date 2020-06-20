# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

from traits.api import Any, HasStrictTraits, Instance, List, on_trait_change

from traits_futures.api import (
    FutureState,
    ProgressFuture,
    CANCELLED,
    CANCELLING,
    COMPLETED,
    EXECUTING,
    FAILED,
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
    except BaseException:
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

    @on_trait_change("future:state")
    def record_state_change(self, obj, name, old_state, new_state):
        if not self.states:
            # On the first state change, record the initial state as well as
            # the new one.
            self.states.append(old_state)
        self.states.append(new_state)

    @on_trait_change("future:progress")
    def record_progress(self, progress_info):
        self.progress.append(progress_info)


class BackgroundProgressTests:
    def test_progress(self):
        # Straightforward case.
        future = self.executor.submit_progress(
            progress_reporting_sum, [1, 2, 3]
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
            self.executor.submit_progress(
                progress_reporting_sum, [1, 2, 3], progress=None
            )

    def test_failed_progress(self):
        # Callable that raises.
        future = self.executor.submit_progress(bad_progress_reporting_function)
        listener = ProgressFutureListener(future=future)

        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertException(future, ZeroDivisionError)
        self.assertEqual(listener.states, [WAITING, EXECUTING, FAILED])

        expected_progress = [(5, 10)]
        self.assertEqual(listener.progress, expected_progress)

    def test_cancellation_before_execution(self):
        event = self.Event()

        future = self.executor.submit_progress(event_set_with_progress, event)
        listener = ProgressFutureListener(future=future)

        self.assertTrue(event.wait(timeout=TIMEOUT))
        self.assertTrue(future.cancellable)
        future.cancel()
        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states, [WAITING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_background_task_starts(self):
        # Test case where the background job is cancelled before
        # it even starts executing.
        event = self.Event()

        with self.block_worker_pool():
            future = self.executor.submit_progress(
                event_set_with_progress, event
            )
            listener = ProgressFutureListener(future=future)
            future.cancel()

        self.wait_until_done(future)

        self.assertFalse(event.is_set())

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(listener.states, [WAITING, CANCELLING, CANCELLED])

    def test_progress_allows_cancellation(self):
        test_ready = self.Event()
        raised = self.Event()

        future = self.executor.submit_progress(
            syncing_progress, test_ready, raised
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
        future = self.executor.submit_progress(progress_reporting_sum, [1, 2])
        self.assertTrue(future.cancellable)
        future.cancel()

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

    def test_cancel_raising_task(self):
        signal = self.Event()
        future = self.executor.submit_progress(wait_then_fail, signal)

        self.wait_for_state(future, EXECUTING)

        future.cancel()
        signal.set()

        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)

    def test_progress_messages_after_cancellation(self):
        signal = self.Event()
        future = self.executor.submit_progress(progress_then_signal, signal)
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
        acquired = self.Event()
        ready = self.Event()
        checkpoint = self.Event()

        try:
            future = self.executor.submit_progress(
                resource_acquirer, acquired, ready, checkpoint
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
        executor.stop()
        self.run_until(executor, "stopped", lambda executor: executor.stopped)
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
        self.assertEqual(future.exception[0], str(exc_type))