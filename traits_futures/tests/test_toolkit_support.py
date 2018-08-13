from __future__ import absolute_import, print_function, unicode_literals

import unittest

from traits.api import HasTraits

from traits_futures.toolkit_support import (
    gui_test_assistant,
    message_receiver,
    message_router,
)


class TestToolkitSupport(unittest.TestCase):
    def test_gui_test_assistant(self):
        GuiTestAssistant = gui_test_assistant()
        test_assistant = GuiTestAssistant()
        self.assertTrue(hasattr(test_assistant, "run_until"))

    def test_message_router_class(self):
        MessageRouter = message_router()
        router = MessageRouter()
        self.assertIsInstance(router, HasTraits)

    def test_message_receiver_class(self):
        MessageReceiver = message_receiver()
        receiver = MessageReceiver()
        self.assertIsInstance(receiver, HasTraits)
