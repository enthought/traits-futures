from __future__ import absolute_import, print_function, unicode_literals

import unittest
import warnings

import mock
import pkg_resources

from traits.api import HasTraits

from traits_futures.toolkit_support import (
    message_router_class,
    message_router_class_for_toolkit,
    MESSAGE_ROUTER_GROUP,
)


class TestToolkitSupport(unittest.TestCase):
    def test_message_router_class(self):
        class_ = message_router_class()
        message_router = class_()
        self.assertIsInstance(message_router, HasTraits)

    def test_message_router_class_bad_toolkit(self):
        with self.assertRaises(RuntimeError):
            message_router_class_for_toolkit("bogus")

    def test_message_router_class_multiple_toolkits(self):
        with mock.patch.object(pkg_resources, 'iter_entry_points') as mock_iep:
            entry_point1 = mock.Mock()
            entry_point2 = mock.Mock()
            mock_iep.return_value = [entry_point1, entry_point2]

            toolkit = "dummy"
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always", RuntimeWarning)
                message_router_class_for_toolkit(toolkit)

            self.assertEqual(len(w), 1)
            warning_message = str(w[0].message)
            self.assertIn("Multiple", warning_message)
            self.assertIn(MESSAGE_ROUTER_GROUP, warning_message)
            self.assertIn(toolkit, warning_message)
