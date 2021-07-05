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
Tests for the Wx GUI context.
"""


import unittest

from traits_futures.testing.optional_dependencies import requires_wx
from traits_futures.tests.i_gui_context_tests import IEventLoopTests


@requires_wx
class TestWxContext(IEventLoopTests, unittest.TestCase):

    #: Factory for instances of the context
    def context_factory(self):
        """Factory for instances of the context."""
        from traits_futures.wx.context import WxContext

        return WxContext()
