# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

from __future__ import absolute_import, print_function, unicode_literals

import unittest

from traits.api import HasTraits

from traits_futures.toolkit_support import (
    message_router_class,
)


class TestToolkitSupport(unittest.TestCase):
    def test_message_router_class(self):
        router_class = message_router_class()
        message_router = router_class()
        self.assertIsInstance(message_router, HasTraits)
