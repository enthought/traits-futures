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
Interface for the toolkit-specific pingee and pinger classes.
"""

import abc


class IPingee(abc.ABC):
    """
    Interface for toolkit-specific pingee classes.

    An IPingee instance provides a toolkit-specific cross-thread pinging
    mechanism. The pingee is owned by the main thread, but may be shared
    with background threads for the sole purpose of allowing those background
    threads to create linked pingers.

    Whenever a ping is received from a linked ``IPinger`` instance, the pingee
    ensures that under a running event loop, the ``on_ping`` callable is
    eventually called. The ``on_ping`` callable will always be called on the
    main thread.

    Parameters
    ----------
    on_ping : callable
        Zero-argument callable that's called on the main thread
        every time a ping is received.
    """

    @abc.abstractmethod
    def connect(self):
        """
        Prepare pingee to receive pings.

        Not thread-safe. This method should only be called in the main thread.
        """

    @abc.abstractmethod
    def disconnect(self):
        """
        Undo any connections made in the connect method.

        Not thread-safe. This method should only be called in the main thread.
        """
        del self._event_loop


class IPinger(abc.ABC):
    """
    Interface for toolkit-specific pinger classes.

    An IPinger instance emits pings targeting a particular IPingee instance.

    Parameters
    ----------
    pingee : IPingee
        The target receiver for the pings. The receiver should already
        be connected.
    """

    @abc.abstractmethod
    def connect(self):
        """
        Connect to the ping receiver. No pings should be sent before
        this method is called.
        """

    @abc.abstractmethod
    def disconnect(self):
        """
        Disconnect from the ping receiver. No pings should be sent after
        calling this method.
        """

    @abc.abstractmethod
    def ping(self):
        """
        Send a ping to the receiver.
        """
