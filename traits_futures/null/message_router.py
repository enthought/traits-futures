# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Support for routing message streams from background processes to their
corresponding foreground receivers.
"""
from traits.api import Any, Event, HasStrictTraits, Instance

from traits_futures.null.package_globals import get_event_loop


#: Prefix used for custom messages
CUSTOM = "custom"


class MessageReceiver(HasStrictTraits):
    """
    Main-thread object that receives messages from a MessageSender.
    """

    #: Event fired when a message is received from the paired sender.
    message = Event(Any())

    def _on_message(self, message):
        """
        Callback fired by the event loop on each message arrival.
        """
        self.message = message


class MessageSender:
    """
    Object allowing the worker to send messages.

    This class will be instantiated in the main thread, but passed to the
    worker thread to allow the worker to communicate back to the main
    thread.

    Only the worker thread should use the send method, and only
    inside a "with sender:" block.
    """

    def __init__(self, async_message, async_done):
        self.async_message = async_message
        self.async_done = async_done

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.async_done()
        self.close()

    def close(self):
        """
        Close this sender.
        """
        self.async_message.close()
        self.async_done.close()

    def send(self, message):
        """
        Send a message to the router.
        """
        self.async_message(message)

    def send_message(self, message_type, message_args=None):
        """
        Send a message from the background task to the router.

        Parameters
        ----------
        message_type : str
            The type of the message
        message_args : any, optional
            Any arguments for the message; ideally, this should be an
            immutable, pickleable object. If not given, ``None`` is used.
        """
        self.send((message_type, message_args))

    def send_custom_message(self, message_type, message_args=None):
        self.send((CUSTOM, message_type, message_args))


class MessageRouter(HasStrictTraits):
    """
    Router for messages from background jobs to their corresponding futures.
    """

    #: Event fired when a receiver is dropped from the routing table.
    receiver_done = Event(Instance(MessageReceiver))

    #: The event loop used for message routing.
    _event_loop = Any()

    def connect(self):
        """
        Connect to the current event loop.
        """
        self._event_loop = get_event_loop()

    def disconnect(self):
        """
        Disconnect from the event loop.
        """
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
        event_loop = self._event_loop
        receiver = MessageReceiver()
        sender = MessageSender(
            async_message=event_loop.async_caller(receiver._on_message),
            async_done=event_loop.async_caller(
                lambda: self._on_done(receiver)
            ),
        )
        return sender, receiver

    def close_pipe(self, sender, receiver):
        """
        Discard an unused sender / receiver pair.
        """
        sender.close()

    def _on_done(self, receiver):
        self.receiver_done = receiver
