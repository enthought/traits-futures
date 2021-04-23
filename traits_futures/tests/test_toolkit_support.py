# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

import unittest

try:
    # importlib.metadata only exists from Python 3.8 onwards. For earlier
    # versions of Python, we use the PyPI package instead.
    import importlib.metadata as importlib_metadata
except ImportError:
    import importlib_metadata

from pyface.base_toolkit import Toolkit

from traits_futures.testing.optional_dependencies import (
    requires_qt,
    requires_wx,
)
from traits_futures.toolkit_support import toolkit

#: Name of the setuptools entry point group for Traits Futures toolkits
TOOLKIT_ENTRY_POINT_GROUP = "traits_futures.toolkits"


class TestToolkitSupport(unittest.TestCase):
    def test_asyncio_entry_points(self):
        self.assertValidToolkitEntryPoint("asyncio")
        self.assertValidToolkitEntryPoint("null")

    @requires_wx
    def test_wx_entry_point(self):
        self.assertValidToolkitEntryPoint("wx")

    @requires_qt
    def test_qt_entry_points(self):
        self.assertValidToolkitEntryPoint("qt")
        self.assertValidToolkitEntryPoint("qt4")

    def test_gui_test_assistant(self):
        GuiTestAssistant = toolkit("gui_test_assistant:GuiTestAssistant")
        test_assistant = GuiTestAssistant()
        self.assertTrue(hasattr(test_assistant, "run_until"))

    def test_pinger_class(self):
        Pingee = toolkit("pingee:Pingee")

        pingee = Pingee(on_ping=lambda: None)
        pinger = pingee.pinger()
        self.assertTrue(hasattr(pinger, "ping"))

    # Helper functions

    def toolkit_entry_points(self, name):
        """
        Return all entry points for the "traits_futures.toolkits" toolkit
        with the given name.

        Parameters
        ----------
        name : str
            Name of the entry point (for example "qt", or "asyncio").

        Returns
        -------
        entry_points : list of importlib.metadata.EntryPoint
            All entry points found whose name is the given one.
        """
        return [
            entry_point
            for entry_point in importlib_metadata.entry_points()[
                TOOLKIT_ENTRY_POINT_GROUP
            ]
            if entry_point.name == name
        ]

    def assertValidToolkitEntryPoint(self, name):
        """
        Check that an entry point with the given name exists,
        that its ``load`` method is functional, and that the
        instantiated object is an instance of Toolkit.
        """
        entry_points = self.toolkit_entry_points(name)
        self.assertEqual(len(entry_points), 1)
        entry_point = entry_points[0]
        toolkit = entry_point.load()
        self.assertIsInstance(toolkit, Toolkit)
