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
# Force an ImportError if wxPython is not installed.
import wx  # noqa: F401

from pyface.base_toolkit import Toolkit

from traits_futures.wx.pinger import Pingee


class WxToolkit(Toolkit):
    def pingee(self, on_ping):
        """
        Return a new Pingee instance for this toolkit.
        """
        return Pingee(on_ping=on_ping)


#: The toolkit object used to find toolkit-specific resources
toolkit_object = WxToolkit("traits_futures", "wx", "traits_futures.wx")
