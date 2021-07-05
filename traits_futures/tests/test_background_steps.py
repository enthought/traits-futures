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
Tests for the background steps task.
"""


import unittest

from traits_futures.api import (
    MultithreadingContext,
    StepsFuture,
    TraitsExecutor,
)
from traits_futures.testing.gui_test_assistant import GuiTestAssistant
from traits_futures.tests.background_steps_tests import BackgroundStepsTests
from traits_futures.tests.common_future_tests import CommonFutureTests


class TestBackgroundSteps(
    GuiTestAssistant, BackgroundStepsTests, unittest.TestCase
):
    def setUp(self):
        GuiTestAssistant.setUp(self)
        self._context = MultithreadingContext()
        self.executor = TraitsExecutor(
            context=self._context,
            event_loop=self._event_loop,
        )

    def tearDown(self):
        self.halt_executor()
        self._context.close()
        GuiTestAssistant.tearDown(self)


class TestStepsFuture(CommonFutureTests, unittest.TestCase):
    def setUp(self):
        self.future_class = StepsFuture
