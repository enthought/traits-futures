# (C) Copyright 2018-2023 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Interface for toolkit-specific event-loop details.
"""

import abc


class IEventLoop(abc.ABC):
    """
    Interface for toolkit-specific event-loop details.

    An instance of this class provides consistent mechanisms to get
    objects related to a particular event loop (for example, that provided
    by a GUI toolkit).
    """

    @abc.abstractmethod
    def pingee(self, on_ping):
        """
        Return a new pingee.

        Parameters
        ----------
        on_ping
            Zero-argument callable, called on the main thread (under a running
            event loop) as a result of each ping sent. The return value of the
            callable is ignored.

        Returns
        -------
        pingee : IPingee
        """

    @abc.abstractmethod
    def helper(self):
        """
        Return a new event loop helper.

        Returns
        -------
        event_loop_helper : IEventLoopHelper
        """
