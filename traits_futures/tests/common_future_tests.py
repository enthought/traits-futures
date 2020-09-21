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
Test methods run for all future types.
"""
from traits.api import Any, Bool, HasStrictTraits, List, on_trait_change, Tuple

from traits_futures.api import IFuture
from traits_futures.base_future import _StateTransitionError
from traits_futures.exception_handling import marshal_exception
from traits_futures.future_states import CANCELLABLE_STATES, DONE_STATES


def dummy_cancel_callback():
    """
    Dummy callback for cancellation, that does nothing.
    """


class FutureListener(HasStrictTraits):
    """ Record state changes to a given future. """

    #: The future that we're listening to.
    future = Any()

    #: Changes to the 'cancellable' trait.
    cancellable_changes = List(Tuple(Bool(), Bool()))

    #: Changes to the 'done' trait.
    done_changes = List(Tuple(Bool(), Bool()))

    @on_trait_change("future:cancellable")
    def _record_cancellable_change(self, object, name, old, new):
        self.cancellable_changes.append((old, new))

    @on_trait_change("future:done")
    def _record_done_change(self, object, name, old, new):
        self.done_changes.append((old, new))


class CommonFutureTests:
    """
    Mixin class providing tests that are run for all future types.
    """

    def test_cancellable_and_done_consistent_with_state(self):
        # Triples (state, cancellable, done)
        states = []

        def record_states():
            """ Record the future's state and derived traits. """
            states.append((future.state, future.cancellable, future.done))

        # Record state when any of the three traits changes.
        future = self.future_class()
        future._executor_initialized(dummy_cancel_callback)

        future.on_trait_change(record_states, "cancellable")
        future.on_trait_change(record_states, "done")
        future.on_trait_change(record_states, "state")

        # Record initial, synthesize some state changes, then record final.
        record_states()
        future._task_started(None)
        future._task_returned(self.fake_exception())
        record_states()

        # Check consistency.
        for state, cancellable, done in states:
            self.assertEqual(cancellable, state in CANCELLABLE_STATES)
            self.assertEqual(done, state in DONE_STATES)

    def test_cancellable_and_done_success(self):
        future = self.future_class()
        future._executor_initialized(dummy_cancel_callback)

        listener = FutureListener(future=future)

        future._task_started(None)
        future._task_returned(23)

        self.assertEqual(listener.cancellable_changes, [(True, False)])
        self.assertEqual(listener.done_changes, [(False, True)])

    def test_cancellable_and_done_failure(self):
        future = self.future_class()
        future._executor_initialized(dummy_cancel_callback)

        listener = FutureListener(future=future)

        future._task_started(None)
        future._task_raised(self.fake_exception())

        self.assertEqual(listener.cancellable_changes, [(True, False)])
        self.assertEqual(listener.done_changes, [(False, True)])

    def test_cancellable_and_done_cancellation(self):
        future = self.future_class()
        future._executor_initialized(dummy_cancel_callback)

        listener = FutureListener(future=future)

        future._task_started(None)
        future._user_cancelled()
        future._task_returned(23)

        self.assertEqual(listener.cancellable_changes, [(True, False)])
        self.assertEqual(listener.done_changes, [(False, True)])

    def test_cancellable_and_done_early_cancellation(self):
        future = self.future_class()
        future._executor_initialized(dummy_cancel_callback)

        listener = FutureListener(future=future)

        future._user_cancelled()
        future._task_started(None)
        future._task_returned(23)

        self.assertEqual(listener.cancellable_changes, [(True, False)])
        self.assertEqual(listener.done_changes, [(False, True)])

    # Tests for the various possible message sequences.

    # The BaseFuture processes four different messages: started / raised /
    # returned messages from the task, and a possible cancellation message from
    # the user. We denote these with the letters S, X (for eXception), R and C,
    # and add machinery to test various combinations. We also write I to
    # denote initialization of the future.

    def test_invalid_message_sequences(self):
        # A future must always be initialized before anything else happens, and
        # then a complete run must always involve "started, raised" or
        # "started, returned" in that order. In addition, a single cancellation
        # is possible at any time before the end of the sequence.
        complete_valid_sequences = {
            "ISR",
            "ISX",
            "ICSR",
            "ICSX",
            "ISCR",
            "ISCX",
        }

        # Systematically generate invalid sequences of messages.
        valid_initial_sequences = {
            seq[:i]
            for seq in complete_valid_sequences
            for i in range(len(seq) + 1)
        }
        continuations = {
            seq[:i] + msg
            for seq in valid_initial_sequences
            for i in range(len(seq) + 1)
            for msg in "ICRSX"
        }
        invalid_sequences = continuations - valid_initial_sequences

        # Check that all invalid sequences raise StateTransitionError
        for sequence in invalid_sequences:
            with self.subTest(sequence=sequence):
                with self.assertRaises(_StateTransitionError):
                    self.send_message_sequence(sequence)

        # Check all complete valid sequences.
        for sequence in complete_valid_sequences:
            with self.subTest(sequence=sequence):
                future = self.send_message_sequence(sequence)
                self.assertTrue(future.done)

    def test_interface(self):
        future = self.future_class()
        self.assertIsInstance(future, IFuture)

    def send_message(self, future, message):
        """ Send a particular message to a future. """
        if message == "I":
            future._executor_initialized(dummy_cancel_callback)
        elif message == "S":
            future._task_started(None)
        elif message == "X":
            future._task_raised(self.fake_exception())
        elif message == "R":
            future._task_returned(23)
        else:
            assert message == "C"
            future._user_cancelled()

    def send_message_sequence(self, messages):
        """ Create a new future, and send the given message sequence to it. """
        future = self.future_class()
        for message in messages:
            self.send_message(future, message)
        return future

    def fake_exception(self):
        """
        Return a marshalled exception similar to that returned on task failure.
        """
        try:
            1 / 0
        except Exception as e:
            return marshal_exception(e)
