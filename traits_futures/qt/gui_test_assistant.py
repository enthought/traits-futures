from __future__ import absolute_import, print_function, unicode_literals

from pyface.ui.qt4.util.gui_test_assistant import (
    GuiTestAssistant as PyFaceGuiTestAssistant)
from traits.testing.unittest_tools import _TraitsChangeCollector as \
    TraitsChangeCollector


class GuiTestAssistant(PyFaceGuiTestAssistant):
    def run_until(self, object, trait, condition, timeout=10.0):
        """
        Run the event loop until the given condition holds true. The condition
        is re-evaluated whenever object.trait changes, and takes the object
        as a parameter.
        """
        collector = TraitsChangeCollector(obj=object, trait=trait)

        collector.start_collecting()
        try:
            self.event_loop_helper.event_loop_until_condition(
                lambda: condition(object), timeout=timeout)
        finally:
            collector.stop_collecting()
