# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Entry point for finding toolkit specific classes.
"""
from pyface.base_toolkit import Toolkit

#: The toolkit object used to find toolkit-specific reources.
toolkit_object = Toolkit("traits_futures", "null", "traits_futures.null")
