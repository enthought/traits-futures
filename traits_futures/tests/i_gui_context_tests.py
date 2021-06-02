# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

""" Mixin tests for testing implementations of IGuiContext. """

from traits_futures.i_event_loop_helper import IEventLoopHelper
from traits_futures.i_gui_context import IGuiContext
from traits_futures.i_pingee import IPingee


class IGuiContextTests:
    """Mixin providing tests for implementations of IGuiContext."""

    #: Override this in subclasses.
    context_factory = IGuiContext

    def setUp(self):
        self.context = self.context_factory()

    def tearDown(self):
        del self.context

    def test_implements_i_gui_context(self):
        self.assertIsInstance(self.context, IGuiContext)

    def test_pingee(self):
        pingee = self.context.pingee(on_ping=lambda: None)
        self.assertIsInstance(pingee, IPingee)

    def test_event_loop_helper(self):
        event_loop_helper = self.context.event_loop_helper()
        self.assertIsInstance(event_loop_helper, IEventLoopHelper)
