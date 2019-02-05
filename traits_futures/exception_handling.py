# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Support for transferring exception information from a background task.
"""
from __future__ import absolute_import, print_function, unicode_literals

import traceback

import six


def marshal_exception(e):
    """
    Turn exception details into something that can be safely
    transmitted across thread / process boundaries.
    """
    exc_type = six.text_type(type(e))
    exc_value = six.text_type(e)
    formatted_traceback = six.text_type(traceback.format_exc())
    return exc_type, exc_value, formatted_traceback
