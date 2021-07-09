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
Tests for the MultithreadingRouter class.
"""

import unittest

from traits_futures.multithreading_context import MultithreadingContext
from traits_futures.testing.test_assistant import TestAssistant
from traits_futures.tests.i_message_router_tests import IMessageRouterTests


class TestMultithreadingRouter(
    TestAssistant, IMessageRouterTests, unittest.TestCase
):
    """
    Test that MultithreadingRouter implements the IMessageRouter interface.
    """

    #: Factory providing the parallelism context
    def context_factory(self):
        return MultithreadingContext()

    def setUp(self):
        TestAssistant.setUp(self)
        IMessageRouterTests.setUp(self)

    def tearDown(self):
        IMessageRouterTests.tearDown(self)
        TestAssistant.tearDown(self)
