"""
Support for toolkit-specific classes.
"""
from __future__ import absolute_import, print_function, unicode_literals

from pyface.base_toolkit import find_toolkit


class Toolkit(object):
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
