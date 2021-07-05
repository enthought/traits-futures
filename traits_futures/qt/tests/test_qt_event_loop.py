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
Tests for the Qt event loop.
"""


import unittest

from traits_futures.testing.optional_dependencies import requires_qt
from traits_futures.tests.i_event_loop_tests import IEventLoopTests


@requires_qt
class TestQtEventLoop(IEventLoopTests, unittest.TestCase):
    def event_loop_factory(self):
        """Factory for instances of the event loop."""
        from traits_futures.qt.event_loop import QtEventLoop

        return QtEventLoop()
