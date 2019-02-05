# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Tests for the GuiTestAssistant.
"""
from __future__ import absolute_import, print_function, unicode_literals

import time
import unittest

from traits.api import Event, HasStrictTraits

from traits_futures.api import CANCELLED, TraitsExecutor
from traits_futures.toolkit_support import toolkit


GuiTestAssistant = toolkit("gui_test_assistant:GuiTestAssistant")


class Dummy(HasStrictTraits):
    never_fired = Event()


class TestGuiTestAssistant(GuiTestAssistant, unittest.TestCase):
    def setUp(self):
        GuiTestAssistant.setUp(self)

    def tearDown(self):
        GuiTestAssistant.tearDown(self)

    def test_run_until_timeout(self):
        # Trait never fired, condition never true.
        dummy = Dummy()
        with self.assertRaises(RuntimeError):
            self.run_until(
                dummy,
                "never_fired",
                condition=lambda object: False,
                timeout=0.1,
            )

    def test_run_until_timeout_trait_fired(self):
        # Trait fired, but condition still never true.
        executor = TraitsExecutor()
        future = executor.submit_call(int, "111")
        with self.assertRaises(RuntimeError):
            self.run_until(
                future,
                "state",
                condition=lambda future: future.state == CANCELLED,
                timeout=0.1,
            )

        executor.stop()
        self.run_until(
            executor,
            "stopped",
            condition=lambda executor: executor.stopped,
        )

    def test_run_until_timeout_with_true_condition(self):
        # Trait never fired, but condition true anyway.
        dummy = Dummy()
        self.run_until(
            dummy,
            "never_fired",
            condition=lambda object: True,
            timeout=10.0,
        )

    def test_run_until_success(self):
        # Trait fired, condition starts false but becomes true.
        def target():
            time.sleep(0.1)
            return 1729

        executor = TraitsExecutor()

        # Case 1: condition true on second trait change event.
        future = executor.submit_call(target)
        self.run_until(
            future,
            "state",
            condition=lambda future: future.done,
        )
        self.assertTrue(future.done)

        # Case 2: condition true on the first trait firing.
        executor.stop()
        self.run_until(
            executor,
            "stopped",
            condition=lambda executor: executor.stopped,
        )
        self.assertTrue(executor.stopped)