# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Tests for ability to subclass the BaseFuture base class.
"""

import unittest

from traits.api import Int, List

from traits_futures.base_future import _StateTransitionError, BaseFuture
from traits_futures.tests.common_future_tests import CommonFutureTests


def dummy_cancel_callback():
    """
    Dummy callback for cancellation, that does nothing.
    """


class PingFuture(BaseFuture):
    """
    BaseFuture subclass that interpretes "ping"
    messages from the background.
    """

    #: Accumulate ping messages
    pings = List(Int)

    def _process_ping(self, arg):
        """
        Process a 'ping' message.
        """
        self.pings.append(arg)


class TestBaseFuture(CommonFutureTests, unittest.TestCase):
    def setUp(self):
        self.future_class = PingFuture

    def test_normal_lifecycle(self):
        future = self.future_class()
        future._executor_initialized(dummy_cancel_callback)
        future._task_started(None)
        future._dispatch_message(("ping", 123))
        future._dispatch_message(("ping", 999))
        future._task_returned(1729)

        self.assertEqual(future.pings, [123, 999])

    def test_ping_after_cancellation_is_ignored(self):
        message = ("ping", 32)

        future = self.future_class()
        future._executor_initialized(dummy_cancel_callback)

        future._task_started(None)
        future._user_cancelled()

        future._dispatch_message(message)
        future._task_returned(1729)

        self.assertEqual(future.pings, [])

    def test_impossible_ping(self):
        # Custom messages should only ever arrive when a future is
        # in EXECUTING or CANCELLING states.
        message = ("ping", 32)

        future = self.future_class()

        with self.assertRaises(_StateTransitionError):
            future._dispatch_message(message)

        future._executor_initialized(dummy_cancel_callback)

        with self.assertRaises(_StateTransitionError):
            future._dispatch_message(message)

        future._task_started(None)
        future._task_returned(1729)

        with self.assertRaises(_StateTransitionError):
            future._dispatch_message(message)

    def test_impossible_ping_cancelled_task(self):
        message = ("ping", 32)

        future = self.future_class()
        future._executor_initialized(dummy_cancel_callback)

        future._user_cancelled()

        with self.assertRaises(_StateTransitionError):
            future._dispatch_message(message)
