# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Interface for toolkit-specific event loop helper class.
"""

import abc


class IEventLoopHelper(abc.ABC):
    """
    Interface for toolkit-specific event loop helper class.

    An IEventLoopHelper instance provides a way to run the event loop
    programmatically until a given condition occurs. Its primary use
    is in testing.
    """

    def init(self):
        """
        Prepare the event loop for use.

        This method is not thread-safe. It should always be called on the
        main GUI thread.
        """

    def dispose(self):
        """
        Dispose of any resources used by this object.

        This method is not thread-safe. It should always be called on the
        main GUI thread.
        """

    def run_until(self, object, trait, condition, timeout):
        """
        Run event loop until a given condition occurs, or timeout.

        The condition is re-evaluated, with the object as argument, every time
        the trait changes.

        This method is not thread-safe. It should always be called on the
        main GUI thread.

        Parameters
        ----------
        object : traits.has_traits.HasTraits
            Object whose trait we monitor.
        trait : str
            Name of the trait to monitor for changes.
        condition : callable
            Single-argument callable, returning a boolean. This will be
            called with *object* as the only input.
        timeout : float
            Number of seconds to allow before timing out with an exception.

        Raises
        ------
        RuntimeError
            If timeout is reached, regardless of whether the condition is
            true or not at that point.
        """
