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


class DummyMessageRouter(HasTraits):
    pass


class AnotherDummyMessageRouter(HasTraits):
    pass


def entry_point(cls, toolkit):
    """
    Temporary entry point for one of the dummy classes above.
    """
    dist = pkg_resources.get_distribution('traits_futures')
    return pkg_resources.EntryPoint.parse(
        '{} = {}:{}'.format(toolkit, __name__, cls.__name__), dist)


class TestToolkitSupport(unittest.TestCase):
    def test_message_router_class(self):
        router_class = message_router_class()
        message_router = router_class()
        self.assertIsInstance(message_router, HasTraits)

    def test_message_router_class_bad_toolkit(self):
        with self.assertRaises(RuntimeError):
            message_router_class_for_toolkit("bogus")

    def test_message_router_class_multiple_toolkits(self):
        toolkit = "dummy"

        with mock.patch.object(pkg_resources, 'iter_entry_points') as mock_iep:
            mock_iep.return_value = [
                entry_point(DummyMessageRouter, toolkit),
                entry_point(AnotherDummyMessageRouter, toolkit),
            ]
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always", RuntimeWarning)
                router_class = message_router_class_for_toolkit(toolkit)

        self.assertEqual(len(w), 1)
        warning_message = str(w[0].message)
        self.assertIn("Multiple", warning_message)
        self.assertIn(MESSAGE_ROUTER_GROUP, warning_message)
        self.assertIn(toolkit, warning_message)

        message_router = router_class()
        self.assertIsInstance(message_router, DummyMessageRouter)
