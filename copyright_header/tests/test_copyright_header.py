# (C) Copyright 2005-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

import unittest

from copyright_header import (
    copyright_header,
    MissingCopyrightHeaderError,
    OutdatedCopyrightYearError,
)


class TestCopyrightHeader(unittest.TestCase):
    def test_good_copyright(self):
        file_contents = """\
# (C) Copyright 2005-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!
"""
        lines = file_contents.splitlines(keepends=True)
        errors = list(copyright_header(lines, minimum_end_year=2020))
        self.assertEqual(len(errors), 0)

    def test_empty_file(self):
        file_contents = ""
        lines = file_contents.splitlines(keepends=True)
        errors = list(copyright_header(lines, minimum_end_year=2020))
        self.assertEqual(len(errors), 0)

    def test_missing_copyright(self):
        file_contents = """\
# This Python file doesn't start with a copyright statement.

import math

x = math.sqrt(1729)
"""
        lines = file_contents.splitlines(keepends=True)
        errors = list(copyright_header(lines, minimum_end_year=2020))
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertIsInstance(error, MissingCopyrightHeaderError)
        self.assertEqual(error.lineno, 1)
        self.assertEqual(error.col_offset, 0)
        self.assertTrue(
            error.full_message.startswith(MissingCopyrightHeaderError.code)
        )
        self.assertIn(
            "header is missing, or doesn't match", error.full_message
        )

    def test_well_formed_copyright_with_out_of_date_year(self):
        file_contents = """\
# (C) Copyright 2005-2010 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!
"""
        lines = file_contents.splitlines(keepends=True)
        errors = list(copyright_header(lines, minimum_end_year=2020))
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertIsInstance(error, OutdatedCopyrightYearError)
        self.assertEqual(error.lineno, 1)
        self.assertEqual(error.col_offset, 16)
        self.assertTrue(
            error.full_message.startswith(OutdatedCopyrightYearError.code)
        )
        self.assertIn("end year (2010) out of date", error.full_message)
