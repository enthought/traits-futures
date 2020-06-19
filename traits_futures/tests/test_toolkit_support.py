# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

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
