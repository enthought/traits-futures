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
Support for toolkit-specific classes.
"""


class Toolkit:
    """
    Provide access to toolkit-specific classes.

    This is a wrapper around the real toolkit object. The first time it's
    used it'll fix the UI backend.
    """

    def __init__(self):
        self._toolkit_object = None

    @property
    def toolkit_object(self):
        from pyface.base_toolkit import find_toolkit

        if self._toolkit_object is None:
            toolkit_class = find_toolkit("traits_futures.toolkits")
            self._toolkit_object = toolkit_class()
        return self._toolkit_object

    def pingee(self, on_ping):
        return self.toolkit_object.pingee(on_ping=on_ping)

    def event_loop_helper(self):
        return self.toolkit_object.event_loop_helper()


#: Object providing access to the current toolkit.
toolkit = Toolkit()
