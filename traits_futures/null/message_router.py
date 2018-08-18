"""
Support for routing message streams from background processes to their
corresponding foreground receivers.
"""
from __future__ import absolute_import, print_function, unicode_literals

from traits.api import Any, Event, HasStrictTraits

from traits_futures.null.package_globals import get_event_loop


class MessageReceiver(HasStrictTraits):
    """
    Main-thread object that receives messages from a MessageSender.
    """
    #: Event fired when a message is received from the paired sender.
    message = Event(Any())

    #: Event fired to indicate that the sender has sent its last message.
    done = Event()

    def _on_message(self, message):
        """
        Callback fired by the event loop on each message arrival.
        """
        self.message = message

    def _on_done(self):
        """
        Callback fired by the event loop indicating no more messages pending.
        """
        self.done = True


class MessageSender(object):
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
        self.async_message.close()
        self.async_done.close()

    def send(self, message):
        """
        Send a message to the router.
        """
        self.async_message(message)


class MessageRouter(object):
    """
    Router for messages from background jobs to their corresponding futures.
    """
    def __init__(self):
        #: The event loop we'll use for message routing.
        self._event_loop = None

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
            async_done=event_loop.async_caller(receiver._on_done),
        )
        return sender, receiver
