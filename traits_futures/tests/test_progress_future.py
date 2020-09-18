# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

import unittest

from traits_futures.api import ProgressFuture
from traits_futures.tests.common_future_tests import CommonFutureTests


class TestProgressFuture(CommonFutureTests, unittest.TestCase):
    def setUp(self):
        self.future_class = ProgressFuture
