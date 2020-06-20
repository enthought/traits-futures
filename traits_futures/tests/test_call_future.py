# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

import unittest

from traits_futures.api import CallFuture
from traits_futures.tests.common_future_tests import CommonFutureTests


class TestCallFuture(CommonFutureTests, unittest.TestCase):
    def setUp(self):
        self.future_class = CallFuture
