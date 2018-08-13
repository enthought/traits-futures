"""
Entry point for finding toolkit-specific classes.
"""
from __future__ import absolute_import, print_function, unicode_literals

from pyface.base_toolkit import Toolkit
# Force an ImportError if Qt is not installed.
from pyface.qt import QtCore  # noqa: F401

#: The toolkit object used to find toolkit-specific reources.
toolkit_object = Toolkit("traits_futures", "qt", "traits_futures.qt")
