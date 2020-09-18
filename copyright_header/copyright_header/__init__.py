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
Copyright header checker

This file provides a checker for the presence and accuracy of the Enthought
open source copyright header in all Python source files, along with
a flake8 wrapper that makes the check available as a flake8 plugin.
"""

import datetime
import re

#: Regular expression to match things of the form "1985" or of the form
#: "1985-1999".
YEAR_RANGE = r"(?P<start_year>\d{4})(?:\-(?P<end_year>\d{4}))?"

#: Pattern (as a regular expression) for the ETS copyright header.
ETS_COPYRIGHT_HEADER_PATTERN = r"""
# \(C\) Copyright {year_range} Enthought, Inc\., Austin, TX
# All rights reserved\.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE\.txt and may be redistributed only under
# the conditions described in the aforementioned license\. The license
# is also available online at http://www\.enthought\.com/licenses/BSD\.txt
#
# Thanks for using Enthought open source!
""".format(
    year_range=YEAR_RANGE
).lstrip()


def parse_year_range(header_text):
    """
    Parse a copyright year range from a header string.

    Looks for a year range of the form "1985" or "1985-1999", and
    returns the start and end year.

    If there are multiple year ranges, parses only the first.

    Parameters
    ----------
    header_text : str
        The text to be parsed. Could be the entire copyright header,
        or a single line from the copyright header.

    Returns
    -------
    start_year, end_year : int
        Start year and end year described by the range.
    match_pos : int
        Position within the string at which the match occurred. This
        is useful for error reporting.

    Raises
    ------
    ValueError
        If no year range is recognised from the given string.
    """
    years_match = re.search(YEAR_RANGE, header_text)
    if not years_match:
        raise ValueError("No year range found in the given string.")

    start_year = int(years_match.group("start_year"))
    end_year_str = years_match.group("end_year")
    end_year = int(end_year_str) if end_year_str is not None else start_year
    return start_year, end_year, years_match.start()


class HeaderError:
    """
    Base class for the copyright header errors.
    """

    def __init__(self, lineno, col_offset):
        self.lineno = lineno
        self.col_offset = col_offset

    @property
    def full_message(self):
        """
        Full message in the form expected by flake8 (including the error code).
        """
        return "{} {}".format(self.code, self.message)


class MissingCopyrightHeaderError(HeaderError):
    """
    Error reported when copyright header is missing, or doesn't match
    the expected wording.
    """

    code = "H101"
    message = (
        "Copyright header is missing, or doesn't match the expected wording."
    )


class BadCopyrightEndYearError(HeaderError):
    """
    Error reported if the copyright header doesn't have the correct
    year information in it.
    """

    code = "H102"

    def __init__(self, lineno, col_offset, actual_end_year, expected_end_year):
        super().__init__(lineno=lineno, col_offset=col_offset)
        self.actual_end_year = actual_end_year
        self.expected_end_year = expected_end_year

    @property
    def message(self):
        return "Copyright end year ({}) should be {}.".format(
            self.actual_end_year, self.expected_end_year
        )


def copyright_header(lines, end_year):
    """
    Check copyright header presence in a Python file.

    Parameters
    ----------
    lines : list of string
        The individual lines from the Python file, each terminated with
        a newline character.
    end_year : int
        Expected end year, for example 2020.

    Yields
    ------
    HeaderError
        Errors found while checking the copyright header.
    """
    file_contents = "".join(lines)

    # Empty files don't need a copyright header.
    if not file_contents:
        return

    # Check that the file starts with the right copyright statement.
    header_match = re.match(ETS_COPYRIGHT_HEADER_PATTERN, file_contents)
    if header_match is None:
        yield MissingCopyrightHeaderError(lineno=1, col_offset=0)
        return

    # Check the year range in the header.
    _, actual_end_year, match_pos = parse_year_range(lines[0])
    if actual_end_year != end_year:
        yield BadCopyrightEndYearError(
            lineno=1,
            col_offset=match_pos,
            actual_end_year=actual_end_year,
            expected_end_year=end_year,
        )


class CopyrightHeaderExtension(object):
    """
    Flake8 extension for checking ETS copyright headers.
    """

    name = "headers"
    version = "1.2.0"

    def __init__(self, tree, lines):
        self.lines = lines

    @classmethod
    def add_options(cls, option_manager):
        option_manager.add_option(
            "--copyright-end-year",
            type="int",
            metavar="year",
            default=datetime.datetime.today().year,
            parse_from_config=True,
            help=(
                "Expected end year in copyright statements "
                "(default is the current year)"
            ),
        )

    @classmethod
    def parse_options(cls, options):
        cls.copyright_end_year = options.copyright_end_year

    def run(self):
        end_year = self.copyright_end_year
        for error in copyright_header(self.lines, end_year=end_year):
            yield (
                error.lineno,
                error.col_offset,
                error.full_message,
                type(self),
            )
