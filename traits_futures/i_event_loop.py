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
Interface for GUI toolkit context objects.
"""

import abc


class IEventLoop(abc.ABC):
    """
    Interface for objects usable in a GUI context.

    An instance of this class provides consistent mechanisms to get
    objects related to the event loop for a particular choice of GUI
    toolkit or event loop.
    """

    @abc.abstractmethod
    def pingee(self, on_ping):
        """
        Return a new pingee.

        Parameters
        ----------
        on_ping : callable
            Zero-argument callable, called on the main thread (under a running
            event loop) as a result of each ping sent. The return value of the
            callable is ignored.

        Returns
        -------
        pingee : IPingee
        """

    @abc.abstractmethod
    def event_loop_helper(self):
        """
        Return a new event loop helper.

        Returns
        -------
        event_loop_helper : IEventLoopHelper
        """
