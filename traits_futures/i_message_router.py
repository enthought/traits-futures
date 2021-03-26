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
Interfaces for message routers, senders and receivers.

Background: messages from background tasks arrive in the foreground via
a single channel (usually some flavour of thread-safe or process-safe queue),
and need to be dispatched to the appropriate receiver. The message router
is responsible for that dispatch.

In more detail, an :class:`IMessageRouter` instance is responsible for:

- Creating "pipes". A pipe is a pairs of linked :class:`IMessageSender` and
  :class:`IMessageReceiver` objects that provide communications between a
  background task and a foreground receiver.
- Ensuring that messages are routed appropriately via a running GUI event loop.
- Disposing of pipes on request.

The message routing layer of Traits Futures provides no meaning or structure to
the actual messages passed; that's the job of the next layer up (the futures
layer).


Overview of the APIs
--------------------

An object implementing :class:`IMessageRouter` has :meth:`IMessageRouter.start`
and :meth:`IMessageRouter.stop` methods to start and stop message routing.
Pipes can only be created or disposed of in a running router.

Pipes are created via the :meth:`IMessageRouter.pipe` method, which returns a
pair `(sender: IMessageSender, receiver: IMessageReceiver)`. The sender is
typically then passed to a background task, where its
:meth:`IMessageSender.send` method can be used to send messages to the
foreground receiver. The receiver has a single :attr:`IMessageReceiver.message`
event trait. Objects wishing to receive the messages sent by the sender should
listen to that trait.

A receiver can be "closed" by passing it to the
:meth:`IMessageRouter.close_pipe` method. Any messages arriving from the paired
sender after the receiver is closed will be discarded (and a warning will be
logged for such messages).

The sender object also has a :meth:`IMessageSender.start` method, which
must be called in the background task before the sender can be used to send
messages, and a :meth:`IMessageSender.stop` method, which should also be
called in the background task in order to undo any resources allocated or
connections made in the :meth:`IMessageSender.start` method.

"""

import abc
import contextlib

from traits.api import Any, Event, Interface


# Note: implementations of IMessageRouter and IMessageReceiver are expected to
# be HasTraits classes, so we inherit from the Traits Interface class.
# IMessageSender implementations are not expected to be HasTraits classes:
# since the sender may be transferred to a background task (potentially
# another process), it's deliberately kept as simple as possible to avoid
# difficulties with that transfer (for example, with pickling).


class IMessageSender(contextlib.AbstractContextManager):
    """
    Interface for objects used to send a message to the foreground.

    Typically an IMessageSender instance for a given router is created
    in the main thread by that router and then passed to the appropriate
    background task.
    """

    @abc.abstractmethod
    def start(self):
        """
        Do any setup necessary to prepare for sending messages.

        This method must be called before any messages can be sent
        using the ``send`` method.

        Not thread-safe. The 'start', 'send' and 'stop' methods should
        all be called from the same thread.

        Raises
        ------
        RuntimeError
            If the sender has previously been started.
        """

    @abc.abstractmethod
    def send(self, message):
        """
        Send a message to the router.

        Parameters
        ----------
        message : object
            Typically this will be immutable, small, and pickleable.

        Not thread-safe. The 'start', 'send' and 'stop' methods should
        all be called from the same thread.

        Raises
        ------
        RuntimeError
            If the sender has not been started, or has already been stopped.
        """

    @abc.abstractmethod
    def stop(self):
        """
        Do any teardown.

        After this method has been called, no more messages can be sent.

        Not thread-safe. The 'start', 'send' and 'stop' methods should
        all be called from the same thread.

        Raises
        ------
        RuntimeError
            If the sender has not been started, or has already been stopped.
        """


class IMessageReceiver(Interface):
    """
    Interface for the main-thread message receiver.
    """

    #: Event fired when a message is received from the paired sender.
    message = Event(Any())


class IMessageRouter(Interface):
    """
    Interface for the main-thread message router.
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

        Logs a warning if there are unclosed pipes.

        Not thread safe. Must always be called in the main thread.

        Raises
        ------
        RuntimeError
            If the router was not already running.
        """

    @abc.abstractmethod
    def pipe(self):
        """
        Create a (sender, receiver) pair for sending and receiving messages.

        The sender will be passed to the background task and used to send
        messages, while the receiver remains in the foreground.

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
