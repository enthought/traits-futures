from __future__ import absolute_import, print_function, unicode_literals

import collections
import itertools

from six.moves import queue

from traits.api import Any, Dict, Event, HasStrictTraits, Instance, Int

from traits_futures.null.event_loop import get_event_loop

#: Message put on the event loop to tell the router to process.
MESSAGE_SENT = "message_sent"


class MessageReceiver(HasStrictTraits):
    """
    Main-thread object that receives messages from a MessageSender.
    """
    #: Event fired when a message is received from the paired sender.
    message = Event(Any())

    #: Event fired to indicate that the sender has sent its last message.
    done = Event()


class MessageSender(object):
    """
    Object allowing the worker to send messages.

    This class will be instantiated in the main thread, but passed to the
    worker thread to allow the worker to communicate back to the main
    thread.

    Only the worker thread should use the send method, and only
    inside a "with sender:" block.
    """
    def __init__(self, connection_id, message_queue, event_loop):
        self.connection_id = connection_id
        self.message_queue = message_queue
        self.event_loop = event_loop

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.message_queue.put(("done", self.connection_id))
        self.event_loop.post_event(MESSAGE_SENT)

    def send(self, message):
        """
        Send a message to the router.
        """
        self.message_queue.put(("message", self.connection_id, message))
        self.event_loop.post_event(MESSAGE_SENT)


class MessageRouter(HasStrictTraits):
    def connect(self):
        self._event_loop = get_event_loop()
        self._event_loop.on_trait_change(self._route_message, "event")

    def disconnect(self):
        self._event_loop.on_trait_change(
            self._route_message, "event", remove=True)
        self._event_loop = None

    def pipe(self):
        """
        Create a (sender, receiver) pair for sending messages.
        """
        connection_id = next(self._connection_ids)
        sender = MessageSender(
            connection_id=connection_id,
            message_queue=self._message_queue,
            event_loop=self._event_loop,
        )
        receiver = MessageReceiver()
        self._receivers[connection_id] = receiver
        return sender, receiver

    # Private traits ##########################################################

    #: Reference to the shared event loop.
    _event_loop = Any()

    #: Internal queue for messages from all senders.
    _message_queue = Any()

    #: Source of new connection ids.
    _connection_ids = Instance(collections.Iterator)

    #: Receivers, keyed by connection_id.
    _receivers = Dict(Int(), Any())

    # Private methods #########################################################

    def _route_message(self):
        wrapped_message = self._message_queue.get()
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
