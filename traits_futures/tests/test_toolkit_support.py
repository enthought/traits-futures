# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

import unittest

from traits_futures.toolkit_support import toolkit


class TestToolkitSupport(unittest.TestCase):
    def test_gui_test_assistant(self):
        GuiTestAssistant = toolkit("gui_test_assistant:GuiTestAssistant")
        test_assistant = GuiTestAssistant()
        self.assertTrue(hasattr(test_assistant, "run_until"))

    def test_pinger_class(self):
        Pinger = toolkit("pinger:Pinger")
        Pingee = toolkit("pinger:Pingee")

        pingee = Pingee(on_ping=lambda: None)
        pinger = Pinger(pingee=pingee)
        self.assertTrue(hasattr(pinger, "ping"))
