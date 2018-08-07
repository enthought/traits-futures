"""
Test methods run for all future types.
"""
from __future__ import absolute_import, print_function, unicode_literals

from traits_futures.api import (
    COMPLETED, EXECUTING, FAILED, CANCELLING, CANCELLED)
from traits_futures.future_states import CANCELLABLE_STATES, FINAL_STATES


class CommonFutureTests(object):
    """
    Mixin class providing tests that are run for all future types.
    """
    def test_done_and_cancellable_consistent_with_state(self):
        # Triples of state, done, cancellable
        states = []

        def record_states():
            """ Record the future's state and derived traits. """
            states.append((future.state, future.done, future.cancellable))

        # Record state when any of the three traits changes.
        future = self.future_class()
        future.on_trait_change(record_states, 'done')
        future.on_trait_change(record_states, 'cancellable')
        future.on_trait_change(record_states, 'state')

        # Record initial, synthesize some state changes, then record final.
        record_states()
        future.state = EXECUTING
        future.state = COMPLETED
        record_states()

        # Check consistency.
        for state, done, cancellable in states:
            self.assertEqual(done, state in FINAL_STATES)
            self.assertEqual(cancellable, state in CANCELLABLE_STATES)

    def test_done_and_cancellable_success(self):
        # Check that done and cancellable aren't being fired unnecessarily
        # frequently, and that we get sensible old values.
        cancellables = []
        dones = []

        def record_cancellable(object, name, old, new):
            cancellables.append((old, new))

        def record_done(object, name, old, new):
            dones.append((old, new))

        future = self.future_class()
        future.on_trait_change(record_cancellable, 'cancellable')
        future.on_trait_change(record_done, 'done')
        future.state = EXECUTING
        future.state = COMPLETED

        self.assertEqual(cancellables, [(True, False)])
        self.assertEqual(dones, [(False, True)])

    def test_done_and_cancellable_failure(self):
        cancellables = []
        dones = []

        def record_cancellable(object, name, old, new):
            cancellables.append((old, new))

        def record_done(object, name, old, new):
            dones.append((old, new))

        future = self.future_class()
        future.on_trait_change(record_cancellable, 'cancellable')
        future.on_trait_change(record_done, 'done')
        future.state = EXECUTING
        future.state = FAILED

        self.assertEqual(cancellables, [(True, False)])
        self.assertEqual(dones, [(False, True)])

    def test_done_and_cancellable_cancellation(self):
        cancellables = []
        dones = []

        def record_cancellable(object, name, old, new):
            cancellables.append((old, new))

        def record_done(object, name, old, new):
            dones.append((old, new))

        future = self.future_class()
        future.on_trait_change(record_cancellable, 'cancellable')
        future.on_trait_change(record_done, 'done')
        future.state = EXECUTING
        future.state = CANCELLING
        future.state = CANCELLED

        self.assertEqual(cancellables, [(True, False)])
        self.assertEqual(dones, [(False, True)])

    def test_done_and_cancellable_early_cancellation(self):
        cancellables = []
        dones = []

        def record_cancellable(object, name, old, new):
            cancellables.append((old, new))

        def record_done(object, name, old, new):
            dones.append((old, new))

        future = self.future_class()
        future.on_trait_change(record_cancellable, 'cancellable')
        future.on_trait_change(record_done, 'done')
        future.state = CANCELLING
        future.state = CANCELLED

        self.assertEqual(cancellables, [(True, False)])
        self.assertEqual(dones, [(False, True)])
