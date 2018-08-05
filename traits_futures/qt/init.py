"""
Entry point for finding toolkit-specific classes.
"""
from __future__ import absolute_import, print_function, unicode_literals

# We need to do something here that fails if neither PyQt nor PySide is
# installed, else we'll end up using this toolkit even when wxpython is
# installed and qt is not.
from pyface.ui.qt4.init import (  # noqa: F401
    toolkit_object as pyface_toolkit_object)
from pyface.base_toolkit import Toolkit

# Create the toolkit object.
toolkit_object = Toolkit("traits_futures", "qt", "traits_futures.qt")
