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

import concurrent.futures
import unittest

from traits_futures.multiprocessing_router import MultiprocessingRouter
from traits_futures.tests.i_message_router_tests import IMessageRouterTests
from traits_futures.toolkit_support import toolkit

GuiTestAssistant = toolkit("gui_test_assistant:GuiTestAssistant")


class TestMultiprocessingRouter(
    GuiTestAssistant, IMessageRouterTests, unittest.TestCase
):
    """
    Test that MultiprocessingRouter implements the IMessageRouter interface.
    """

    #: Factory providing the routers under test.
    router_factory = MultiprocessingRouter

    #: Factory providing worker pools for the tests.
    executor_factory = concurrent.futures.ProcessPoolExecutor

    def setUp(self):
        GuiTestAssistant.setUp(self)

    def tearDown(self):
        GuiTestAssistant.tearDown(self)
