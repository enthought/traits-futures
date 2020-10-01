# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

from traits.api import HasStrictTraits, Instance, List, on_trait_change

from traits_futures.api import (
    CallFuture,
    CANCELLED,
    CANCELLING,
    COMPLETED,
    EXECUTING,
    FAILED,
    FutureState,
    submit_call,
    WAITING,
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
        future = submit_call(self.executor, pow, 2, 3)
        listener = CallFutureListener(future=future)

        self.wait_until_done(future)

        self.assertResult(future, 8)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, COMPLETED],
        )

    def test_failed_call(self):
        future = submit_call(self.executor, fail)
        listener = CallFutureListener(future=future)

        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertException(future, ZeroDivisionError)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, FAILED],
        )

    def test_cancellation_vs_started_race_condition(self):
        # Simulate situation where a STARTED message arrives post-cancellation.
        event = self._context.event()

        future = submit_call(self.executor, event.set)
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
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_execution(self):
        # Case where cancellation occurs before the future even starts
        # executing.
        with self.block_worker_pool():
            future = submit_call(self.executor, pow, 2, 3)
            listener = CallFutureListener(future=future)
            self.assertTrue(future.cancellable)
            future.cancel()

        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_success(self):
        signal = self._context.event()
        test_ready = self._context.event()

        future = submit_call(self.executor, ping_pong, signal, test_ready)
        listener = CallFutureListener(future=future)

        # Wait for executing state; the test_ready event ensures we
        # get no further.
        self.assertTrue(signal.wait(timeout=TIMEOUT))
        self.wait_for_state(future, EXECUTING)

        self.assertTrue(future.cancellable)
        future.cancel()
        test_ready.set()
        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cancellation_before_failure(self):
        signal = self._context.event()
        test_ready = self._context.event()

        future = submit_call(self.executor, ping_pong_fail, signal, test_ready)
        listener = CallFutureListener(future=future)

        # Wait for executing state; the test_ready event ensures we
        # get no further.
        self.assertTrue(signal.wait(timeout=TIMEOUT))
        self.wait_for_state(future, EXECUTING)

        self.assertTrue(future.cancellable)
        future.cancel()
        test_ready.set()
        self.wait_until_done(future)

        self.assertNoResult(future)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
        )

    def test_cannot_cancel_after_success(self):
        future = submit_call(self.executor, pow, 2, 3)
        listener = CallFutureListener(future=future)

        self.wait_until_done(future)

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

        self.assertResult(future, 8)
        self.assertNoException(future)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, COMPLETED],
        )

    def test_cannot_cancel_after_failure(self):
        future = submit_call(self.executor, fail)
        listener = CallFutureListener(future=future)

        self.wait_until_done(future)

        self.assertFalse(future.cancellable)
        with self.assertRaises(RuntimeError):
            future.cancel()

        self.assertNoResult(future)
        self.assertException(future, ZeroDivisionError)
        self.assertEqual(
            listener.states,
            [WAITING, EXECUTING, FAILED],
        )

    def test_cannot_cancel_after_cancel(self):
        future = submit_call(self.executor, pow, 2, 3)
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
            listener.states,
            [WAITING, CANCELLING, CANCELLED],
        )

    def test_double_cancel_variant(self):
        signal = self._context.event()
        test_ready = self._context.event()

        future = submit_call(self.executor, ping_pong, signal, test_ready)
        listener = CallFutureListener(future=future)

        # Wait for executing state; the test_ready event ensures we
        # get no further.
        self.assertTrue(signal.wait(timeout=TIMEOUT))
        self.wait_for_state(future, EXECUTING)

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
            listener.states,
            [WAITING, EXECUTING, CANCELLING, CANCELLED],
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
