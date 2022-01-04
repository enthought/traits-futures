# (C) Copyright 2018-2022 Enthought, Inc., Austin, TX
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


def _qualified_type_name(class_):
    """
    Compute a descriptive string representing a class, including
    a module name where relevant.

    Example outputs are "RuntimeError" for the built-in RuntimeError
    exception, or "struct.error" for the struct module exception class.

    Parameters
    ----------
    class_ : type

    Returns
    -------
    class_name : str
    """
    # We're being extra conservative here and allowing for the possibility that
    # the class doesn't have __module__ and/or __qualname__ attributes. This
    # function is called during exception handling, so we want to minimise the
    # possibility that it raises a new exception.
    class_module = getattr(class_, "__module__", "<unknown>")
    class_qualname = getattr(class_, "__qualname__", "<unknown>")
    if class_module == "builtins":
        return f"{class_qualname}"
    else:
        return f"{class_module}.{class_qualname}"


def marshal_exception(exception):
    """
    Turn exception details into something that can be safely
    transmitted across thread / process boundaries.

    Parameters
    ----------
    exception : BaseException
        The exception instance to be marshalled

    Returns
    -------
    exception_type, exception_value, exception_traceback : str
        Strings representing the exception type, value and
        formatted traceback.
    """
    return (
        _qualified_type_name(type(exception)),
        str(exception),
        "".join(
            traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
        ),
    )
