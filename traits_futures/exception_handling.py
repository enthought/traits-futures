# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Support for transferring exception information from a background task.
"""
from __future__ import absolute_import, print_function, unicode_literals

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
