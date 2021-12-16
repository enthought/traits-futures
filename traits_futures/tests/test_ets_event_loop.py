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
Tests for the ETS event loop.
"""


import os
import subprocess
import sys
import unittest

from traits_futures.ets_event_loop import ETSEventLoop
from traits_futures.testing.optional_dependencies import (
    requires_qt,
    requires_wx,
)
from traits_futures.tests.i_event_loop_tests import IEventLoopTests

#: Code snippet to be executed with "python -c" in order to print the toolkit
#: resolved by ETSEventLoop.
PRINT_TOOLKIT = """
from traits_futures.ets_event_loop import ETSEventLoop
try:
    event_loop = ETSEventLoop().toolkit_event_loop
except Exception as e:
    print("Failed:", type(e).__name__)
else:
    print("Loop:", type(event_loop).__name__)
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
        Name of the toolkit event loop class selected.
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


@requires_qt
class TestETSEventLoop(IEventLoopTests, unittest.TestCase):
    #: Factory for instances of the event loop.
    event_loop_factory = ETSEventLoop

    def test_toolkit_choice_cached(self):
        event_loop = ETSEventLoop()
        # Check that we get the same instance both times.
        event_loop1 = event_loop.toolkit_event_loop
        event_loop2 = event_loop.toolkit_event_loop
        self.assertIs(event_loop1, event_loop2)


class TestToolkitSelection(unittest.TestCase):
    @requires_qt
    def test_selects_qt(self):
        self.assertEqual(find_selected_toolkit("qt"), "Loop: QtEventLoop")
        self.assertEqual(find_selected_toolkit("qt4"), "Loop: QtEventLoop")

    @requires_qt
    def test_qt_priority(self):
        # If Qt is present, under current ETS rules it takes priority,
        # regardless of what other toolkits are available.
        self.assertEqual(find_selected_toolkit(), "Loop: QtEventLoop")

    @requires_wx
    def test_selects_wx(self):
        self.assertEqual(find_selected_toolkit("wx"), "Loop: WxEventLoop")

    def test_bogus_value(self):
        self.assertEqual(
            find_selected_toolkit("bogus"), "Failed: RuntimeError"
        )

    def test_no_ets_toolkit_var(self):
        toolkit_event_loop = find_selected_toolkit()
        # We'll get different results depending on the environment that
        # the toolkit selection is performed in.
        self.assertIn(
            toolkit_event_loop,
            [
                "Loop: QtEventLoop",
                "Loop: WxEventLoop",
                "Failed: RuntimeError",
            ],
        )
