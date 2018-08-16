"""
Support for routing message streams from background processes to their
corresponding foreground receivers.
"""
from __future__ import absolute_import, print_function, unicode_literals

import itertools

from traits.api import Any, Event, HasStrictTraits

from traits_futures.null.event_loop import get_event_loop


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
    def __init__(self, connection_id, async_message, async_done):
        self.connection_id = connection_id
        self.async_message = async_message
        self.async_done = async_done

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.async_done(self.connection_id)

    def send(self, message):
        """
        Send a message to the router.
        """
        self.async_message((self.connection_id, message))


class MessageRouter(object):
    """
    Router for messages from background jobs to their corresponding futures.
    """
    def __init__(self):
        self._event_loop = None
        self._async_on_message = None
        self._async_on_done = None
        self._receivers = {}
        self._connection_ids = itertools.count()

    def connect(self):
        """
        Connect to the current event loop.
        """
        self._event_loop = event_loop = get_event_loop()
        self._async_on_message = event_loop.async_caller(self._on_message)
        self._async_on_done = event_loop.async_caller(self._on_done)

    def disconnect(self):
        """
        Disconnect from the event loop.
        """
        self._event_loop.disconnect(self._async_on_done)
        self._async_on_done = None
        self._event_loop.disconnect(self._async_on_message)
        self._async_on_message = None
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
            async_message=self._async_on_message,
            async_done=self._async_on_done,
        )
        self._receivers[connection_id] = receiver = MessageReceiver()
        return sender, receiver

    # Private methods #########################################################

    def _on_message(self, connection_id_and_message):
        connection_id, message = connection_id_and_message
        receiver = self._receivers[connection_id]
        receiver.message = message

    def _on_done(self, connection_id):
        receiver = self._receivers.pop(connection_id)
        receiver.done = True
