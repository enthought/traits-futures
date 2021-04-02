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
Entry point for finding toolkit-specific classes.
"""
# We import QtCore to force an ImportError if Qt is not installed.
from pyface.base_toolkit import Toolkit
from pyface.qt import QtCore  # noqa: F401

from traits_futures.qt.pinger import Pingee


class QtToolkit(Toolkit):
    def pingee(self, on_ping):
        """
        Return a new Pingee instance for this toolkit.
        """
        return Pingee(on_ping=on_ping)


#: The toolkit object used to find toolkit-specific resources.
toolkit_object = QtToolkit("traits_futures", "qt", "traits_futures.qt")
