# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Test support, providing the ability to run the event loop from tests.
"""

from pyface.ui.qt4.util.gui_test_assistant import (
    GuiTestAssistant as PyFaceGuiTestAssistant)


class GuiTestAssistant(PyFaceGuiTestAssistant):
    def run_until(self, object, trait, condition, timeout=10.0):
        """
        Run the event loop until the given condition holds true.
        """
        self.event_loop_helper.event_loop_until_condition(
            lambda: condition, timeout=timeout)
