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
Interface for message routers.

Message routers support sending a properly terminated single-source
single-destination stream of messages from a background task to the foreground.
The message routers know nothing about the future machinery - that's in the
next layer up.

Message routers are responsible for:

- Creating pipes used to send message from a background task to the
  foreground.
- Receiving and dispatching those messages appropriately.
- Disposing of pipes once they're no longer needed.

"""

# XXX Improve docstrings in this file.
# XXX Fix docstrings of implementations to match those
#     of the interface.
# XXX Consider dropping need to call "sender.start";
#     just initialize lazily.

import abc

from traits.api import Interface


class IMessageRouter(Interface):
    """
    Main-thread object that receives and routes messages from the background.
    """

    @abc.abstractmethod
    def start(self):
        """
        Start routing messages.

        This method must be called before any call to ``pipe`` or
        ``close_pipe`` can be made.

        Not thread-safe. Must always be called in the main thread.

        Raises
        ------
        RuntimeError
            If the router has already been started.
        """

    @abc.abstractmethod
    def stop(self):
        """
        Stop routing messages.

        This method should be called in the main thread after all pipes
        are finished with. Calls to ``pipe`` or ``close_pipe`` are
        not permitted after this method has been called.

        Not thread safe. Must always be called in the main thread.

        Raises
        ------
        RuntimeError
            If the router was not already running.
        """

    @abc.abstractmethod
    def pipe(self):
        """
        Create a (sender, receiver) pair for sending messages.

        The sender object is passed to the background task, and
        can then be used by that background task to send messages.

        The receiver has a single trait which is fired when a message is
        received from the background and routed to the receiver.

        Not thread safe. Must always be called in the main thread.

        Returns
        -------
        sender : IMessageSender
            Object to be passed to the background task.
        receiver : IMessageReceiver
            Object kept in the foreground, which reacts to messages.

        Raises
        ------
        RuntimeError
            If the router is not currently running.
        """

    @abc.abstractmethod
    def close_pipe(self, receiver):
        """
        Close the receiver end of a pipe produced by ``pipe``.

        Removes the receiver from the routing table, so that no new messages
        can reach that receiver.

        Not thread safe. Must always be called in the main thread.

        Parameters
        ----------
        receiver : IMessageReceiver
            Receiver half of the pair returned by the ``pipe`` method.

        Raises
        ------
        RuntimeError
            If the router is not currently running.
        """
