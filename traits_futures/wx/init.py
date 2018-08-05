"""
Entry point for finding toolkit-specific classes.
"""
from __future__ import absolute_import, print_function, unicode_literals

from pyface.base_toolkit import Toolkit

# Create the toolkit object.
toolkit_object = Toolkit("traits_futures", "wx", "traits_futures.wx")
