from __future__ import absolute_import, print_function, unicode_literals

import collections
import itertools

from traits.api import Any, Dict, Event, HasStrictTraits, Instance, Int

from traits_futures.null.event_loop import (
    EventLoop, EventPoster, get_event_loop)


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
    def __init__(self, connection_id, event_poster):
        self.connection_id = connection_id
        self.event_poster = event_poster

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        event_args = "done", self.connection_id, True
        self.event_poster.post_event(event_args)

    def send(self, message):
        """
        Send a message to the router.
        """
        event_args = "message", self.connection_id, message
        self.event_poster.post_event(event_args)


class MessageRouter(HasStrictTraits):
    """
    Router for messages from background jobs to their corresponding futures.
    """
    #: Traits event fired whenever an event is received.
    message_sent = Event(Any())

    def connect(self):
        """
        Connect to the current event loop.
        """
        self._event_loop = get_event_loop()
        self._event_poster = self._event_loop.event_poster(
            self, "message_sent")

    def disconnect(self):
        """
        Disconnect from the event loop.
        """
        self._event_loop.disconnect(self._event_poster)
        self._event_poster = None
        self._event_loop = None

    def pipe(self):
        """
        Create a (sender, receiver) pair for sending and receiving messages.

        Returns
        -------
        sender : MessageSender
            Object used by the background threads to send messages.
        receiver : MessageReceiver
            Object used to receive messages sent by the sender.
        """
        connection_id = next(self._connection_ids)
        sender = MessageSender(
            connection_id=connection_id,
            event_poster=self._event_poster,
        )
        self._receivers[connection_id] = receiver = MessageReceiver()
        return sender, receiver

    # Private traits ##########################################################

    #: The event loop that we're posting events to.
    _event_loop = Instance(EventLoop)

    #: Poster for the "message posted" event.
    _event_poster = Instance(EventPoster)

    #: Source of new connection ids.
    _connection_ids = Instance(collections.Iterator)

    #: Receivers, keyed by connection_id.
    _receivers = Dict(Int(), Any())

    # Private methods #########################################################

    def _message_sent_fired(self, event_args):
        message_type, connection_id, message = event_args
        if message_type == "done":
            receiver = self._receivers.pop(connection_id)
        else:
            receiver = self._receivers[connection_id]
        setattr(receiver, message_type, message)

    def __connection_ids_default(self):
        return itertools.count()
