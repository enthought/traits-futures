# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Test methods run for all future types.
"""
from __future__ import absolute_import, print_function, unicode_literals

from traits.api import Any, Bool, HasStrictTraits, List, on_trait_change, Tuple

from traits_futures.api import (
    CANCELLED, CANCELLING, COMPLETED, EXECUTING, FAILED)
from traits_futures.future_states import CANCELLABLE_STATES, DONE_STATES


class FutureListener(HasStrictTraits):
    """ Record state changes to a given future. """

    #: The future that we're listening to.
    future = Any()

    #: Changes to the 'cancellable' trait.
    cancellable_changes = List(Tuple(Bool(), Bool()))

    #: Changes to the 'done' trait.
    done_changes = List(Tuple(Bool(), Bool()))

    @on_trait_change('future:cancellable')
    def _record_cancellable_change(self, object, name, old, new):
        self.cancellable_changes.append((old, new))

    @on_trait_change('future:done')
    def _record_done_change(self, object, name, old, new):
        self.done_changes.append((old, new))


class CommonFutureTests(object):
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
        future.on_trait_change(record_states, 'cancellable')
        future.on_trait_change(record_states, 'done')
        future.on_trait_change(record_states, 'state')

        # Record initial, synthesize some state changes, then record final.
        record_states()
        future.state = EXECUTING
        future.state = COMPLETED
        record_states()

        # Check consistency.
        for state, cancellable, done in states:
            self.assertEqual(cancellable, state in CANCELLABLE_STATES)
            self.assertEqual(done, state in DONE_STATES)

    def test_cancellable_and_done_success(self):
        future = self.future_class()
        listener = FutureListener(future=future)

        future.state = EXECUTING
        future.state = COMPLETED

        self.assertEqual(listener.cancellable_changes, [(True, False)])
        self.assertEqual(listener.done_changes, [(False, True)])

    def test_cancellable_and_done_failure(self):
        future = self.future_class()
        listener = FutureListener(future=future)

        future.state = EXECUTING
        future.state = FAILED

        self.assertEqual(listener.cancellable_changes, [(True, False)])
        self.assertEqual(listener.done_changes, [(False, True)])

    def test_cancellable_and_done_cancellation(self):
        future = self.future_class()
        listener = FutureListener(future=future)

        future.state = EXECUTING
        future.state = CANCELLING
        future.state = CANCELLED

        self.assertEqual(listener.cancellable_changes, [(True, False)])
        self.assertEqual(listener.done_changes, [(False, True)])

    def test_cancellable_and_done_early_cancellation(self):
        future = self.future_class()
        listener = FutureListener(future=future)

        future.state = CANCELLING
        future.state = CANCELLED

        self.assertEqual(listener.cancellable_changes, [(True, False)])
        self.assertEqual(listener.done_changes, [(False, True)])
