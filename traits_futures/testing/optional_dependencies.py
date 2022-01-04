# (C) Copyright 2018-2022 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Code for managing optional dependencies in tests.
"""

import unittest

try:
    from pyface.qt import QtCore
except ImportError:
    QtCore = None

#: Decorator that can be used to indicate that a test requires a Qt
#: backend (e.g., PyQt or PySide2)
requires_qt = unittest.skipIf(QtCore is None, "Qt not available")


try:
    import wx
except ImportError:
    wx = None

#: Decorator that can be used to indicate that a test requires wxPython.
requires_wx = unittest.skipIf(wx is None, "wx not available")
