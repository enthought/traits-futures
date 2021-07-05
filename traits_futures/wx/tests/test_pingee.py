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
Tests for the Wx implementations of IPingee and IPinger.
"""

import unittest

from traits_futures.testing.gui_test_assistant import GuiTestAssistant
from traits_futures.testing.optional_dependencies import requires_wx
from traits_futures.tests.i_pingee_tests import IPingeeTests


@requires_wx
class TestPingee(GuiTestAssistant, IPingeeTests, unittest.TestCase):
    def gui_context_factory(self):
        from traits_futures.wx.context import WxEventLoop

        return WxEventLoop()
