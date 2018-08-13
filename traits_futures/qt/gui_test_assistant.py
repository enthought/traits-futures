"""
Test support, providing the ability to run the event loop from tests.
"""

from __future__ import absolute_import, print_function, unicode_literals

from pyface.ui.qt4.util.gui_test_assistant import (
    GuiTestAssistant as PyFaceGuiTestAssistant)


class GuiTestAssistant(PyFaceGuiTestAssistant):
    def run_until(self, object, trait, condition, timeout=10.0):
        """
        Run the event loop until the given condition holds true.
        """
        self.event_loop_helper.event_loop_until_condition(
            lambda: condition(object), timeout=timeout)
