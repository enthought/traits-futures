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
Example of testing a simple future using the GuiTestAssistant.
"""

import unittest

from pyface.toolkit import toolkit_object
from traits_futures.api import submit_call, TraitsExecutor


#: Maximum timeout for blocking calls, in seconds. A successful test should
#: never hit this timeout - it's there to prevent a failing test from hanging
#: forever and blocking the rest of the test suite.
SAFETY_TIMEOUT = 5.0


#: Note that the GuiTestAssistant is currently only available for Qt, not
#: for wxPython. To run this unit test, you'll need PyQt or PySide 2 installed.
GuiTestAssistant = toolkit_object("util.gui_test_assistant:GuiTestAssistant")


class TestMyFuture(GuiTestAssistant, unittest.TestCase):
    def setUp(self):
        GuiTestAssistant.setUp(self)
        self.executor = TraitsExecutor()

    def tearDown(self):
        # Request the executor to stop, and wait for that stop to complete.
        self.executor.stop()
        self.assertEventuallyTrueInGui(
            lambda: self.executor.stopped, timeout=SAFETY_TIMEOUT
        )

        GuiTestAssistant.tearDown(self)

    def test_my_future(self):
        executor = self.executor

        future = submit_call(executor, pow, 3, 5)

        # Wait for the future to complete.
        self.assertEventuallyTrueInGui(
            lambda: future.done, timeout=SAFETY_TIMEOUT
        )

        self.assertEqual(future.result, 243)
