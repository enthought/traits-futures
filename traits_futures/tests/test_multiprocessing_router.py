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
Tests for the MultiprocessingRouter class.
"""

import unittest

from traits_futures.multiprocessing_context import MultiprocessingContext
from traits_futures.tests.i_message_router_tests import IMessageRouterTests
from traits_futures.toolkit_support import toolkit

GuiTestAssistant = toolkit("gui_test_assistant:GuiTestAssistant")


class TestMultiprocessingRouter(
    GuiTestAssistant, IMessageRouterTests, unittest.TestCase
):
    """
    Test that MultiprocessingRouter implements the IMessageRouter interface.
    """

    #: Factory providing the parallelism context
    context_factory = MultiprocessingContext

    def setUp(self):
        GuiTestAssistant.setUp(self)
        IMessageRouterTests.setUp(self)

    def tearDown(self):
        IMessageRouterTests.tearDown(self)
        GuiTestAssistant.tearDown(self)
