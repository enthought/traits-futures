# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

import unittest

from traits_futures.toolkit_support import toolkit


class TestToolkitSupport(unittest.TestCase):
    def test_event_loop_helper(self):
        EventLoopHelper = toolkit("event_loop_helper:EventLoopHelper")
        event_loop_helper = EventLoopHelper()
        self.assertTrue(hasattr(event_loop_helper, "run_until"))

    def test_pinger_class(self):
        pingee = toolkit.pingee(on_ping=lambda: None)
        pinger = pingee.pinger()
        self.assertTrue(hasattr(pinger, "ping"))
