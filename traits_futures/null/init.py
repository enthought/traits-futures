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
Entry point for finding toolkit specific classes.
"""
from pyface.base_toolkit import Toolkit

#: The toolkit object used to find toolkit-specific reources.
toolkit_object = Toolkit("traits_futures", "null", "traits_futures.null")
