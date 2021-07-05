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
Tests for the asyncio GUI context.
"""


import unittest

from traits_futures.asyncio.context import AsyncioEventLoop
from traits_futures.tests.i_gui_context_tests import IEventLoopTests


class TestAsyncioEventLoop(IEventLoopTests, unittest.TestCase):

    #: Factory for instances of the context.
    context_factory = AsyncioEventLoop
