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
Event loop with toolkit selection matching that of ETS.

This module provides an IEventLoop implementation that's determined in the
same way that the toolkit is determined for TraitsUI and Pyface, using the
ETS_TOOLKIT environment variable if set, and examining the available toolkits
if not.
"""

from traits_futures.i_event_loop import IEventLoop


@IEventLoop.register
class ETSEventLoop:
    """
    IEventLoop implementation with lazily-determined toolkit.

    The first time this event loop is used, an appropriate toolkit will
    be selected.

    The toolkit selection mechanism used matches that used by Pyface, and
    is based on the value of the ETS_TOOLKIT environment variable, followed
    an examination of the available setuptools entry points under the
    entry point group "traits_futures.event_loops".

    """

    def __init__(self):
        self._toolkit_event_loop = None

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
        return self.toolkit_event_loop.pingee(on_ping)

    def event_loop_helper(self):
        """
        Return a new event loop helper.

        Returns
        -------
        event_loop_helper : IEventLoopHelper
        """
        return self.toolkit_event_loop.event_loop_helper()

    @property
    def toolkit_event_loop(self):
        """
        Find and fix the toolkit, using the same mechanism that Pyface uses to
        find its toolkits.
        """
        from pyface.base_toolkit import find_toolkit

        if self._toolkit_event_loop is None:
            toolkit_event_loop_class = find_toolkit(
                "traits_futures.event_loops"
            )
            self._toolkit_event_loop = toolkit_event_loop_class()

        return self._toolkit_event_loop
