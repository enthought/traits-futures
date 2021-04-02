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
Testing helpers and utilities.
"""

import unittest

from traits_futures.testing.gui_test_assistant import (
    GuiTestAssistant,
    SAFETY_TIMEOUT,
)

try:
    from pyface.qt import QtCore
except ImportError:
    QtCore = None
requires_qt = unittest.skipIf(QtCore is None, "Qt not available")


try:
    import wx
except ImportError:
    wx = None
requires_wx = unittest.skipIf(wx is None, "wx not available")


__all__ = [
    "GuiTestAssistant",
    "SAFETY_TIMEOUT",
    "requires_qt",
    "requires_wx",
]
