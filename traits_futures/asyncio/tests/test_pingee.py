# (C) Copyright 2018-2023 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Tests for the asyncio implementations of IPingee and IPinger.
"""

import asyncio
import unittest

from traits_futures.asyncio.event_loop import AsyncioEventLoop
from traits_futures.testing.test_assistant import TestAssistant
from traits_futures.tests.i_pingee_tests import IPingeeTests


class TestPingee(TestAssistant, IPingeeTests, unittest.TestCase):
    def event_loop_factory(self):
        """
        Factory for the event loop.

        Returns
        -------
        event_loop: IEventLoop
        """
        asyncio_event_loop = asyncio.new_event_loop()
        self.addCleanup(asyncio_event_loop.close)
        return AsyncioEventLoop(event_loop=asyncio_event_loop)
