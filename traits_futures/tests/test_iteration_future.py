# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Tests for the IterationFuture class.
"""
import unittest

from traits_futures.api import IterationFuture
from traits_futures.tests.common_future_tests import CommonFutureTests


class TestIterationFuture(CommonFutureTests, unittest.TestCase):
    def setUp(self):
        self.future_class = IterationFuture
