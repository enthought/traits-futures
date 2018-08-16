from __future__ import absolute_import, print_function, unicode_literals

import unittest

from traits_futures.toolkit_support import toolkit


class TestToolkitSupport(unittest.TestCase):
    def test_gui_test_assistant(self):
        GuiTestAssistant = toolkit("gui_test_assistant:GuiTestAssistant")
        test_assistant = GuiTestAssistant()
        self.assertTrue(hasattr(test_assistant, "run_until"))

    def test_message_router_class(self):
        MessageRouter = toolkit("message_router:MessageRouter")
        router = MessageRouter()
        self.assertTrue(hasattr(router, "pipe"))
