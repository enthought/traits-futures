"""
Support for toolkit-specific classes.
"""
from __future__ import absolute_import, print_function, unicode_literals

from pyface.base_toolkit import find_toolkit


def message_router_class():
    toolkit_object = find_toolkit("traits_futures.toolkits")
    return toolkit_object("message_router:MessageRouter")


def gui_test_assistant_class():
    toolkit_object = find_toolkit("traits_futures.toolkits")
    return toolkit_object("gui_test_assistant:GuiTestAssistant")
