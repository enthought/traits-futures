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
Tests for the asyncio implementation of IEventLoopHelper.
"""

import unittest

from traits_futures.asyncio.event_loop import AsyncioEventLoop
from traits_futures.tests.i_event_loop_helper_tests import (
    IEventLoopHelperTests,
)


class TestEventLoopHelper(IEventLoopHelperTests, unittest.TestCase):
    def event_loop_factory(self):
        """
        Factory for the event loop.

        Returns
        -------
        event_loop: IEventLoop
        """
        event_loop = AsyncioEventLoop()
        self.addCleanup(event_loop.close)
        return event_loop
