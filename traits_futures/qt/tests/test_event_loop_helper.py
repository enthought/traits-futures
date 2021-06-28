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
Tests for the Qt implementation of IEventLoopHelper.
"""

import unittest

from traits_futures.testing.optional_dependencies import requires_qt
from traits_futures.tests.i_event_loop_helper_tests import (
    IEventLoopHelperTests,
)


@requires_qt
class TestEventLoopHelper(IEventLoopHelperTests, unittest.TestCase):
    def gui_context_factory(self):
        """Create a suitable IGuiContext instance."""
        from traits_futures.qt.context import QtContext

        return QtContext()
