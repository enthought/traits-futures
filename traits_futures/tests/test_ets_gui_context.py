# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Tests for the ETS gui context.
"""


import os
import subprocess
import sys
import unittest

from traits_futures.ets_context import ETSEventLoop
from traits_futures.testing.optional_dependencies import (
    requires_qt,
    requires_wx,
)
from traits_futures.tests.i_event_loop_tests import IEventLoopTests

#: Code snippet to be executed with "python -c" in order to print the toolkit
#: resolved by ETSEventLoop.
PRINT_TOOLKIT = """
from traits_futures.ets_context import ETSEventLoop
print(type(ETSEventLoop().toolkit_context).__name__)
"""


def find_selected_toolkit(ets_toolkit=None):
    """
    Return the toolkit that's selected for a given value of the
    ETS_TOOLKIT environment variable.

    Parameters
    ----------
    ets_toolkit : str
        Value of the ETS_TOOLKIT environment variable.

    Returns
    -------
    selected_toolkit : str
        Name of the toolkit context class selected.
    """
    env = os.environ.copy()
    env.pop("ETS_TOOLKIT", None)
    if ets_toolkit is not None:
        env["ETS_TOOLKIT"] = ets_toolkit

    process = subprocess.run(
        [sys.executable, "-c", PRINT_TOOLKIT],
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        env=env,
    )
    return process.stdout.rstrip()


class TestETSEventLoop(IEventLoopTests, unittest.TestCase):
    #: Factory for instances of the context.
    context_factory = ETSEventLoop


class TestToolkitSelection(unittest.TestCase):
    @requires_qt
    def test_selects_qt(self):
        self.assertEqual(find_selected_toolkit("qt"), "QtEventLoop")
        self.assertEqual(find_selected_toolkit("qt4"), "QtEventLoop")

    @requires_wx
    def test_selects_wx(self):
        self.assertEqual(find_selected_toolkit("wx"), "WxEventLoop")

    def test_null_selects_asyncio(self):
        self.assertEqual(find_selected_toolkit("asyncio"), "AsyncioEventLoop")
        self.assertEqual(find_selected_toolkit("null"), "AsyncioEventLoop")

    def test_no_ets_toolkit_var(self):
        toolkit_context = find_selected_toolkit()
        # We'll get different results depending on the environment that
        # the toolkit selection is performed in.
        self.assertIn(
            toolkit_context, ["QtEventLoop", "WxEventLoop", "AsyncioEventLoop"]
        )
