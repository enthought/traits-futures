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

Message routers are responsible for:

- Creating pipes used to send message from a background task to the
  foreground.
- Receiving and dispatching those messages appropriately.
"""


import abc

from traits.api import Interface


class IMessageRouter(Interface):
    """
    Main-thread object that receives and routes messages from the background.
    """

    @abc.abstractmethod
    def pipe(self):
        """
        Create a (sender, receiver) pair for sending messages.

        The sender object is passed to the background task, and
        can then be used by that background task to send messages.

        The receiver has a single trait which is fired when a message is
        received from the background and routed to the receiver.

        Not thread safe.

        Returns
        -------
        sender : IMessageSender
            Object to be passed to the background task.
        receiver : MessageReceiver
            Object kept in the foreground, which reacts to messages.
        """

    @abc.abstractmethod
    def close_pipe(self, sender, receiver):
        """
        Close an unused pipe.

        This is used for example when a pipe is created and something else
        subsequently goes wrong (for example, creation of the background
        task fails).

        Not thread safe.

        Parameters
        ----------
        sender : IMessageSender
            First item of a pair produced by the ``pipe`` method.
        receiver : MessageReceiver
            Second item of a pair produced by the ``pipe`` method.
        """

    @abc.abstractmethod
    def connect(self):
        """
        Prepare router for routing.

        This method should be called in the main thread before all calls to
        ``pipe`` or ``close_pipe``.

        Not thread-safe.
        """

    @abc.abstractmethod
    def disconnect(self):
        """
        Undo any connections made by the ``connect`` call.

        This method should be called in the main thread after all pipes
        are finished with.

        Not thread safe.
        """
