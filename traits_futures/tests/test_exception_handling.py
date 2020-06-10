# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

from __future__ import absolute_import, print_function, unicode_literals

import unittest

from traits_futures.exception_handling import marshal_exception


class TestExceptionHandling(unittest.TestCase):
    def test_marshal_exception(self):
        try:
            raise RuntimeError("something went wrong")
        except BaseException as exception:
            marshalled = marshal_exception(exception)

        exc_type, exc_value, exc_traceback = marshalled
        self.assertIsInstance(exc_type, str)
        self.assertIsInstance(exc_value, str)
        self.assertIsInstance(exc_traceback, str)

        self.assertEqual(exc_type, str(RuntimeError))
        self.assertIn("something went wrong", exc_value)
        self.assertIn("test_marshal_exception", exc_traceback)

    def test_marshal_exception_with_unicode_message(self):
        message = "temperature too high: 104\N{DEGREE SIGN}"
        try:
            raise ValueError("temperature too high: 104\N{DEGREE SIGN}")
        except BaseException as exception:
            marshalled = marshal_exception(exception)

        exc_type, exc_value, exc_traceback = marshalled
        self.assertIsInstance(exc_type, str)
        self.assertIsInstance(exc_value, str)
        self.assertIsInstance(exc_traceback, str)

        self.assertEqual(exc_type, str(ValueError))
        self.assertIn(message, exc_value)
        self.assertIn("test_marshal_exception", exc_traceback)
