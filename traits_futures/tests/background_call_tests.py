# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

from traits.api import HasStrictTraits, Instance, List, on_trait_change

from traits_futures.api import (
    CallFuture,
    FutureState,
    CANCELLED,
    CANCELLING,
    DONE,
    EXECUTING,
)


#: Timeout for blocking operations, in seconds.
TIMEOUT = 10.0


def ping_pong(ping_event, pong_event):
    """
    Send a ping, then wait for an answering pong.
    """
    ping_event.set()
    pong_event.wait(timeout=TIMEOUT)


def ping_pong_fail(ping_event, pong_event):
    """
    Send a ping, wait for an answering pong, then fail.
    """
    ping_event.set()
    pong_event.wait(timeout=TIMEOUT)
    1 / 0


def fail():
    """
    Callable that fails with an exception.
    """
    1 / 0


class CallFutureListener(HasStrictTraits):
    #: Future that we're listening to.
    future = Instance(CallFuture)

    #: List of states of that future.
    states = List(FutureState)

    @on_trait_change("future:state")
    def record_state_change(self, obj, name, old_state, new_state):
        if not self.states:
            # On the first state change, record the initial state as well as
            # the new one.
            self.states.append(old_state)
        self.states.append(new_state)


class BackgroundCallTests:
    """ Mixin class containing tests for the background call. """

    def test_successful_call(self):
        future = self.executor.submit_call(pow, 2, 3)
        listener = CallFutureListener(future=future)

        self.wait_until_done(future)

        self.assertResult(future, 8)
        self.assertNoException(future)
        self.assertEqual(
            listener.states, [EXECUTING, DONE],
        )
        self.assertTrue(future.ok)

    def test_failed_call(self):
        future = self.executor.submit_call(fail)
        listener = CallFutureListener(future=future)

        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertException(future, ZeroDivisionError)
        self.assertEqual(
            listener.states, [EXECUTING, DONE],
        )
        self.assertFalse(future.ok)

    def test_cancellation_vs_started_race_condition(self):
        # Simulate situation where we start executing post-cancellation.
        event = self.Event()

        future = self.executor.submit_call(event.set)
        listener = CallFutureListener(future=future)

        # Ensure the background task is past the cancel_event.is_set() check.
        self.assertTrue(event.wait(timeout=TIMEOUT))

        # And _now_ cancel before we process any messages.
        self.assertTrue(future.cancellable)
        future.cancel()
        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states, [EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_execution(self):
        # Case where cancellation occurs before the future even starts
        # executing.
        with self.block_worker_pool():
            future = self.executor.submit_call(pow, 2, 3)
            listener = CallFutureListener(future=future)
            self.assertTrue(future.cancellable)
            future.cancel()

        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states, [EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_success(self):
        signal = self.Event()
        test_ready = self.Event()

        future = self.executor.submit_call(ping_pong, signal, test_ready)
        listener = CallFutureListener(future=future)

        # Wait until execution starts; the test_ready event ensures we
        # get no further.
        self.assertTrue(signal.wait(timeout=TIMEOUT))

        self.assertTrue(future.cancellable)
        future.cancel()
        test_ready.set()
        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states, [EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_failure(self):
        signal = self.Event()
        test_ready = self.Event()

        future = self.executor.submit_call(ping_pong_fail, signal, test_ready)
        listener = CallFutureListener(future=future)

        # Wait until execution starts; the test_ready event ensures we
        # get no further.
        self.assertTrue(signal.wait(timeout=TIMEOUT))

        self.assertTrue(future.cancellable)
        future.cancel()
        test_ready.set()
        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states, [EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cannot_cancel_after_success(self):
        future = self.executor.submit_call(pow, 2, 3)
        listener = CallFutureListener(future=future)

        self.wait_until_done(future)

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

        self.assertResult(future, 8)
        self.assertNoException(future)
        self.assertEqual(
            listener.states, [EXECUTING, DONE],
        )
        self.assertTrue(future.ok)

    def test_cannot_cancel_after_failure(self):
        future = self.executor.submit_call(fail)
        listener = CallFutureListener(future=future)

        self.wait_until_done(future)

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

        self.assertNoResult(future)
        self.assertException(future, ZeroDivisionError)
        self.assertEqual(
            listener.states, [EXECUTING, DONE],
        )
        self.assertFalse(future.ok)

    def test_cannot_cancel_after_cancel(self):
        future = self.executor.submit_call(pow, 2, 3)
        listener = CallFutureListener(future=future)

        self.assertTrue(future.cancellable)
        future.cancel()
        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states, [EXECUTING, CANCELLING, CANCELLED],
        )

    def test_double_cancel_variant(self):
        signal = self.Event()
        test_ready = self.Event()

        future = self.executor.submit_call(ping_pong, signal, test_ready)
        listener = CallFutureListener(future=future)

        # Wait until execution starts; the test_ready event ensures we
        # get no further.
        self.assertTrue(signal.wait(timeout=TIMEOUT))

        self.assertTrue(future.cancellable)
        future.cancel()
        test_ready.set()

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states, [EXECUTING, CANCELLING, CANCELLED],
        )

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

    def assertException(self, future, exc_type):
        self.assertEqual(future.exception[0], str(exc_type))

    def assertNoException(self, future):
        with self.assertRaises(AttributeError):
            future.exception
