"""
Entry point for finding toolkit specific classes.
"""
from __future__ import absolute_import, print_function, unicode_literals

from pyface.base_toolkit import Toolkit

#: The toolkit object used to find toolkit-specific reources.
toolkit_object = Toolkit("traits_futures", "null", "traits_futures.null")