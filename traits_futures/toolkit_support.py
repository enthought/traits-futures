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
Support for toolkit-specific classes.
"""
from pyface.base_toolkit import find_toolkit


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
        if self._toolkit_object is None:
            self._toolkit_object = find_toolkit("traits_futures.toolkits")
        return self._toolkit_object

    def __call__(self, name):
        return self.toolkit_object(name)


#: Object providing access to the current toolkit.
toolkit = Toolkit()
