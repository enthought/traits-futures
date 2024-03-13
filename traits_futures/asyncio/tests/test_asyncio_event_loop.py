# (C) Copyright 2018-2024 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Tests for the asyncio event loop.
"""

import asyncio
import unittest

from traits_futures.asyncio.event_loop import AsyncioEventLoop
from traits_futures.tests.i_event_loop_tests import IEventLoopTests


class TestAsyncioEventLoop(IEventLoopTests, unittest.TestCase):
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

    def test_asyncio_event_loop_closed(self):
        with self.assertWarns(DeprecationWarning):
            event_loop = AsyncioEventLoop()
        # Dig out the underlying asyncio event loop.
        asyncio_event_loop = event_loop._event_loop
        self.assertFalse(asyncio_event_loop.is_closed())
        event_loop.close()
        self.assertTrue(asyncio_event_loop.is_closed())

    def test_creation_from_asyncio_event_loop(self):
        asyncio_event_loop = asyncio.new_event_loop()
        event_loop = AsyncioEventLoop(event_loop=asyncio_event_loop)
        self.assertEqual(event_loop._event_loop, asyncio_event_loop)
        try:
            self.assertFalse(asyncio_event_loop.is_closed())
            # Closing our wrapper shouldn't close the asyncio event loop.
            event_loop.close()
            self.assertFalse(asyncio_event_loop.is_closed())
        finally:
            asyncio_event_loop.close()
