# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

import unittest

from traits_futures.api import ProgressFuture
from traits_futures.tests.common_future_tests import CommonFutureTests


class TestProgressFuture(CommonFutureTests, unittest.TestCase):
    def setUp(self):
        self.future_class = ProgressFuture
