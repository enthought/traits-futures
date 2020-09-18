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
Support for transferring exception information from a background task.
"""
import traceback


def marshal_exception(e):
    """
    Turn exception details into something that can be safely
    transmitted across thread / process boundaries.
    """
    exc_type = str(type(e))
    exc_value = str(e)
    formatted_traceback = str(traceback.format_exc())
    return exc_type, exc_value, formatted_traceback
