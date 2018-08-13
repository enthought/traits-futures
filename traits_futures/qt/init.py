"""
Entry point for finding toolkit-specific classes.
"""
from __future__ import absolute_import, print_function, unicode_literals

from pyface.base_toolkit import Toolkit

# Force failure if Qt is not available.
# XXX Find better way to do this. Load the PyFace toolkit object?
from pyface.qt import QtGui

#: The toolkit object used to find toolkit-specific reources.
toolkit_object = Toolkit("traits_futures", "qt", "traits_futures.qt")
