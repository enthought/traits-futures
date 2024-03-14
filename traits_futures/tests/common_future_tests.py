# (C) Copyright 2018-2024 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Test methods run for all future types.
"""
import weakref

from traits.api import Any, Bool, HasStrictTraits, List, observe, Tuple

from traits_futures.api import IFuture
from traits_futures.base_future import _StateTransitionError
from traits_futures.exception_handling import marshal_exception
from traits_futures.future_states import CANCELLABLE_STATES, DONE_STATES


def dummy_cancel_callback():
    """
    Dummy callback for cancellation, that does nothing.
    """


# Set of all possible complete valid sequences of internal state changes
# that a future might encounter. Here:
#
# * A represents the background task being abandoned before starting
# * S represents the background task starting
# * X represents the background task failing with an exception
# * R represents the background task returning a result
# * C represents the user cancelling.
#
# A complete run must always involve "abandoned", "started, raised" or
# "started, returned" in that order. In addition, a single cancellation is
# possible at any time before the end of the sequence, and abandoned can only
# ever occur following cancellation.

MESSAGE_TYPES = "ASRXC"

COMPLETE_VALID_SEQUENCES = {
    "SR",
    "SX",
    "CSR",
    "CSX",
    "SCR",
    "SCX",
    "CA",
}


class FutureListener(HasStrictTraits):
    """Record state changes to a given future."""

    #: The future that we're listening to.
    future = Any()

    #: Changes to the 'cancellable' trait.
    cancellable_changes = List(Tuple(Bool(), Bool()))

    #: Changes to the 'done' trait.
    done_changes = List(Tuple(Bool(), Bool()))

    @observe("future:cancellable")
    def _record_cancellable_change(self, event):
        old, new = event.old, event.new
        self.cancellable_changes.append((old, new))

    @observe("future:done")
    def _record_done_change(self, event):
        old, new = event.old, event.new
        self.done_changes.append((old, new))


class CommonFutureTests:
    """
    Mixin class providing tests that are run for all future types.
    """

    def test_cancellable_and_done_consistent_with_state(self):
        # Triples (state, cancellable, done)
        states = []

        def record_states(event=None):
            """Record the future's state and derived traits."""
            states.append((future.state, future.cancellable, future.done))

        # Record state when any of the three traits changes.
        future = self.future_class(_cancel=dummy_cancel_callback)

        future.observe(record_states, "cancellable")
        future.observe(record_states, "done")
        future.observe(record_states, "state")

        # Record initial, synthesize some state changes, then record final.
        record_states()
        future._task_started(None)
        future._task_returned(23)
        record_states()

        # Check consistency.
        for state, cancellable, done in states:
            self.assertEqual(cancellable, state in CANCELLABLE_STATES)
            self.assertEqual(done, state in DONE_STATES)

    def test_cancellable_and_done_success(self):
        future = self.future_class(_cancel=dummy_cancel_callback)

        listener = FutureListener(future=future)

        future._task_started(None)
        future._task_returned(23)

        self.assertEqual(listener.cancellable_changes, [(True, False)])
        self.assertEqual(listener.done_changes, [(False, True)])

    def test_cancellable_and_done_failure(self):
        future = self.future_class(_cancel=dummy_cancel_callback)

        listener = FutureListener(future=future)

        future._task_started(None)
        future._task_raised(self.fake_exception())

        self.assertEqual(listener.cancellable_changes, [(True, False)])
        self.assertEqual(listener.done_changes, [(False, True)])

    def test_cancellable_and_done_cancellation(self):
        future = self.future_class(_cancel=dummy_cancel_callback)

        listener = FutureListener(future=future)

        future._task_started(None)
        future._user_cancelled()
        future._task_returned(23)

        self.assertEqual(listener.cancellable_changes, [(True, False)])
        self.assertEqual(listener.done_changes, [(False, True)])

    def test_cancellable_and_done_early_cancellation(self):
        future = self.future_class(_cancel=dummy_cancel_callback)

        listener = FutureListener(future=future)

        future._user_cancelled()
        future._task_started(None)
        future._task_returned(23)

        self.assertEqual(listener.cancellable_changes, [(True, False)])
        self.assertEqual(listener.done_changes, [(False, True)])

    def test_invalid_message_sequences(self):
        # Systematically generate invalid sequences of messages.
        valid_initial_sequences = {
            seq[:i]
            for seq in COMPLETE_VALID_SEQUENCES
            for i in range(len(seq) + 1)
        }
        continuations = {
            seq[:i] + msg
            for seq in valid_initial_sequences
            for i in range(len(seq) + 1)
            for msg in MESSAGE_TYPES
        }
        invalid_sequences = continuations - valid_initial_sequences

        # Check that all invalid sequences raise StateTransitionError
        for sequence in invalid_sequences:
            with self.subTest(sequence=sequence):
                with self.assertRaises(_StateTransitionError):
                    self.send_message_sequence(sequence)

        # Check all complete valid sequences.
        for sequence in COMPLETE_VALID_SEQUENCES:
            with self.subTest(sequence=sequence):
                future = self.send_message_sequence(sequence)
                self.assertTrue(future.done)

    def test_cancel_callback_released(self):
        for sequence in COMPLETE_VALID_SEQUENCES:
            with self.subTest(sequence=sequence):

                def do_nothing():
                    return None

                finalizer = weakref.finalize(do_nothing, lambda: None)
                future = self.send_message_sequence(sequence, do_nothing)
                self.assertTrue(future.done)
                self.assertTrue(finalizer.alive)
                del do_nothing
                self.assertFalse(finalizer.alive)

    def test_interface(self):
        future = self.future_class(_cancel=dummy_cancel_callback)
        self.assertIsInstance(future, IFuture)

    def test_zero_argument_instantiation(self):
        # Regression test for enthought/traits-futures#466
        future = self.future_class()
        self.assertIsInstance(future, IFuture)

    def send_message(self, future, message, cancel_callback):
        """Send a particular message to a future."""
        if message == "A":
            future._task_abandoned(None)
        elif message == "S":
            future._task_started(None)
        elif message == "R":
            future._task_returned(23)
        elif message == "X":
            future._task_raised(self.fake_exception())
        elif message == "C":
            future._user_cancelled()
        else:
            raise ValueError(f"message {message} not understood")

    def send_message_sequence(self, messages, cancel_callback=None):
        """Create a new future, and send the given message sequence to it."""
        if cancel_callback is None:
            cancel_callback = dummy_cancel_callback

        future = self.future_class(_cancel=dummy_cancel_callback)
        for message in messages:
            self.send_message(future, message, cancel_callback)
        return future

    def fake_exception(self):
        """
        Return a marshalled exception similar to that returned on task failure.
        """
        try:
            1 / 0
        except Exception as e:
            return marshal_exception(e)
