# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

from __future__ import absolute_import, print_function, unicode_literals

import collections
import itertools

from six.moves import queue

from traits.api import Any, Dict, Event, HasStrictTraits, Instance, Int


class LazyMessageSender(object):
    def __init__(self, connection_id, message_queue):
        self.connection_id = connection_id
        self.message_queue = message_queue

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.message_queue.put(("done", self.connection_id))

    def send(self, message):
        self.message_queue.put(("message", self.connection_id, message))


class LazyMessageReceiver(HasStrictTraits):
    #: Event fired when a message is received from the paired sender.
    message = Event(Any())

    #: Event fired to indicate that the sender has sent its last message.
    done = Event()


class LazyMessageRouter(HasStrictTraits):
    """
    Router for messages. Messages aren't delivered until the router is pumped.
    """
    def pipe(self):
        """
        Create a (sender, receiver) pair for sending messages.

        Returns
        -------
        sender : LazyMessageSender
            Object to be passed to the background task to send messages.
        receiver : LazyMessageReceiver
            Object to be kept in the foreground which reacts to messages.
        """
        connection_id = next(self._connection_ids)
        sender = LazyMessageSender(
            connection_id=connection_id,
            message_queue=self._message_queue,
        )
        receiver = LazyMessageReceiver()
        self._receivers[connection_id] = receiver
        return sender, receiver

    def route_until(self, condition, timeout):
        """
        Route messages until the given condition evaluates to true.
        """
        while not condition():
            self._route_message(timeout=timeout)

    # Private traits ##########################################################

    #: Internal queue for messages from workers.
    _message_queue = Any()

    #: Source of new connection ids.
    _connection_ids = Instance(collections.Iterator)

    #: Receivers, keyed by connection_id.
    _receivers = Dict(Int(), Any())

    # Private methods #########################################################

    def _route_message(self, timeout):
        wrapped_message = self._message_queue.get(timeout=timeout)
        if wrapped_message[0] == "message":
            _, connection_id, message = wrapped_message
            receiver = self._receivers[connection_id]
            receiver.message = message
        else:
            assert wrapped_message[0] == "done"
            _, connection_id = wrapped_message
            receiver = self._receivers.pop(connection_id)
            receiver.done = True

    def __message_queue_default(self):
        return queue.Queue()

    def __connection_ids_default(self):
        return itertools.count()
