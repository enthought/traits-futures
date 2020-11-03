# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Message routing for the null toolkit.

Messages are dispatched onto the asyncio event loop.
"""
import asyncio
import collections.abc
import itertools
import queue

from traits.api import Any, Dict, Event, HasStrictTraits, Instance, Int

from traits_futures.message_receiver import MessageReceiver
from traits_futures.multithreading_sender import MultithreadingSender
from traits_futures.null.pinger import AsyncioPinger


class MessageRouter(HasStrictTraits):
    """
    Router for messages, sent by means of Qt signals and slots.

    Requires the event loop to be running in order for messages to arrive.
    """

    #: Event fired when a receiver is dropped from the routing table.
    receiver_done = Event(Instance(MessageReceiver))

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
        connection_id = next(self._connection_ids)
        pinger = AsyncioPinger(
            asyncio_event_loop=self._event_loop,
            route_message=self._route_message,
        )
        sender = MultithreadingSender(
            connection_id=connection_id,
            pinger=pinger,
            message_queue=self._message_queue,
        )
        receiver = MessageReceiver()
        self._receivers[connection_id] = receiver
        return sender, receiver

    def close_pipe(self, sender, receiver):
        """
        Close an unused pipe.
        """
        connection_id = sender.connection_id
        self._receivers.pop(connection_id)

    def connect(self):
        """
        Prepare router for routing.
        """
        self._event_loop = asyncio.get_event_loop()

    def disconnect(self):
        """
        Undo any connections made by the ``connect`` call.
        """

    # Private traits ##########################################################

    #: Internal queue for messages from all senders.
    _message_queue = Any()

    #: Source of new connection ids.
    _connection_ids = Instance(collections.abc.Iterator)

    #: Receivers, keyed by connection_id.
    _receivers = Dict(Int(), Any())

    #: The event loop used for message routing.
    _event_loop = Any()

    # Private methods #########################################################

    async def _route_message(self):
        wrapped_message = self._message_queue.get()
        if wrapped_message[0] == "message":
            _, connection_id, message = wrapped_message
            receiver = self._receivers[connection_id]
            receiver.message = message
        else:
            assert wrapped_message[0] == "done"
            _, connection_id = wrapped_message
            receiver = self._receivers.pop(connection_id)
            self.receiver_done = receiver

    def __message_queue_default(self):
        return queue.Queue()

    def __connection_ids_default(self):
        return itertools.count()
