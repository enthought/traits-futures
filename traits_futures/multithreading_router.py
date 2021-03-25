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
Implementation of the IMessageRouter interface for the case where the
sender will be in a background thread.
"""

import collections.abc
import itertools
import logging
import queue

from traits.api import (
    Any,
    Bool,
    Dict,
    HasStrictTraits,
    Instance,
    Int,
    provides,
)

from traits_futures.i_message_router import IMessageRouter
from traits_futures.message_receiver import MessageReceiver
from traits_futures.multithreading_sender import MultithreadingSender
from traits_futures.toolkit_support import toolkit

logger = logging.getLogger(__name__)

Pingee = toolkit("pinger:Pingee")
Pinger = toolkit("pinger:Pinger")


@provides(IMessageRouter)
class MultithreadingRouter(HasStrictTraits):
    """
    Implementation of the IMessageRouter interface for the case where the
    sender will be in a background thread.
    """

    def start(self):
        """
        Prepare router for routing.
        """
        if self._running:
            raise RuntimeError("router is already running")

        self._message_queue = queue.Queue()

        self._pingee = Pingee(on_ping=self._route_message)
        self._pingee.connect()

        self._running = True

    def stop(self):
        """
        Undo any connections made by the ``connect`` call.
        """
        if not self._running:
            raise RuntimeError("router is not running")

        if self._receivers:
            logger.warning("there are unclosed pipes")

        self._pingee.disconnect()
        self._pingee = None

        self._message_queue = None

        self._running = False

    def pipe(self):
        """
        Create a (sender, receiver) pair for sending messages.

        Returns
        -------
        sender : MultithreadingSender
            Object to be passed to the background task to send messages.
        receiver : MessageReceiver
            Object to be kept in the foreground which reacts to messages.
        """
        if not self._running:
            raise RuntimeError("router is not running")

        connection_id = next(self._connection_ids)
        pinger = Pinger(pingee=self._pingee)
        sender = MultithreadingSender(
            connection_id=connection_id,
            pinger=pinger,
            message_queue=self._message_queue,
        )
        receiver = MessageReceiver(connection_id=connection_id)
        self._receivers[connection_id] = receiver
        return sender, receiver

    def close_pipe(self, receiver):
        """
        Stop passing on messages to the given receiver, and remove
        the receiver from the routing table.

        Parameters
        ----------
        receiver : MessageReceiver
        """
        if not self._running:
            raise RuntimeError("router is not running")

        connection_id = receiver.connection_id
        self._receivers.pop(connection_id)

    # Private traits ##########################################################

    #: Internal queue for messages from all senders.
    _message_queue = Any()

    #: Source of new connection ids.
    _connection_ids = Instance(collections.abc.Iterator)

    #: Receivers, keyed by connection_id.
    _receivers = Dict(Int(), Any())

    #: Receiver for the "message_sent" signal.
    _pingee = Instance(Pingee)

    #: Router status: True if running, False if stopped.
    _running = Bool(False)

    # Private methods #########################################################

    def _route_message(self):
        connection_id, message = self._message_queue.get()
        try:
            receiver = self._receivers[connection_id]
        except KeyError:
            logger.warning(
                f"No receiver for message with connection_id {connection_id}. "
                "Message discarded."
            )
        else:
            receiver.message = message

    def __connection_ids_default(self):
        return itertools.count()
