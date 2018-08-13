"""
Support for toolkit-specific classes.
"""
from __future__ import absolute_import, print_function, unicode_literals

from pyface.base_toolkit import find_toolkit


class Toolkit(object):
    """
    Provide access to toolkit-specific classes.
    """
    def __init__(self):
        self._toolkit_object = None

    @property
    def toolkit_object(self):
        if self._toolkit_object is None:
            self._toolkit_object = find_toolkit("traits_futures.toolkits")
        return self._toolkit_object

    @property
    def GuiTestAssistant(self):
        """
        Help with testing.
        """
        return self.toolkit_object("gui_test_assistant:GuiTestAssistant")

    @property
    def MessageReceiver(self):
        """
        Main-thread end of a (message_sender, message_receiver) pair.
        """
        return self.toolkit_object("message_router:MessageReceiver")

    @property
    def MessageRouter(self):
        """
        Router for messages from background tasks to futures.
        """
        return self.toolkit_object("message_router:MessageRouter")


def message_receiver():
    """
    MessageReceiver class.
    """
    toolkit_object = find_toolkit("traits_futures.toolkits")
    return toolkit_object("message_router:MessageReceiver")


def message_router():
    """
    MessageRouter class.
    """
    toolkit_object = find_toolkit("traits_futures.toolkits")
    return toolkit_object("message_router:MessageRouter")


def gui_test_assistant():
    """
    GuiTestAssistant class.
    """
    toolkit_object = find_toolkit("traits_futures.toolkits")
    return toolkit_object("gui_test_assistant:GuiTestAssistant")
