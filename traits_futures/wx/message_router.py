from __future__ import absolute_import, print_function, unicode_literals

import collections
import itertools

from six.moves import queue
import wx

from traits.api import Any, Dict, Event, HasStrictTraits, Instance, Int


#: Event type that's unique to this message. (It's just an integer.)
MESSAGE_SENT_EVENT_TYPE = wx.NewEventType()


class MessageSentEvent(wx.PyCommandEvent):
    """ wx event used to signal that a message has been sent """
    def __init__(self, event_id):
        wx.PyCommandEvent.__init__(self, MESSAGE_SENT_EVENT_TYPE, event_id)


class _MessageSignallee(wx.EvtHandler):
    """
    Event handler object for messages to be sent to.

    This object stays in the main thread.
    """
    def bind_to_callback(self, callback):
        """
        Bind the MESSAGE_SENT_EVENT_TYPE event to the given callback.
        """
        self.binder = wx.PyEventBinder(MESSAGE_SENT_EVENT_TYPE, 1)
        self.Bind(self.binder, callback)

    def unbind(self):
        """
        Undo the binding made in ``bind_to_callback``.
        """
        self.Unbind(self.binder)
        self.binder = None


class MessageSender(object):
    """
    Object allowing the worker to send messages.

    This class will be instantiated in the main thread, but passed to the
    worker thread to allow the worker to communicate back to the main
    thread.

    Only the worker thread should use the send method, and only
    inside a "with sender:" block.
    """
    def __init__(self, connection_id, signallee, message_queue):
        self.connection_id = connection_id
        self.signallee = signallee
        self.message_queue = message_queue

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.message_queue.put(("done", self.connection_id))
        wx.PostEvent(self.signallee, MessageSentEvent(-1))
        del self.signallee

    def send(self, message):
        """
        Send a message to the router.
        """
        self.message_queue.put(("message", self.connection_id, message))
        wx.PostEvent(self.signallee, MessageSentEvent(-1))


class MessageReceiver(HasStrictTraits):
    """
    Main-thread object that receives messages from a MessageSender.
    """
    #: Event fired when a message is received from the paired sender.
    message = Event(Any)

    #: Event fired to indicate that the sender has sent its last message.
    done = Event


class MessageRouter(HasStrictTraits):
    """
    Router for messages, sent by means of Wx events.

    Requires the event loop to be running in order for messages to arrive.
    """
    def pipe(self):
        """
        Create a (sender, receiver) pair for sending messages.

        Returns
        -------
        sender : MessageSender
            Object to be passed to the background task to send messages.
        receiver : MessageReceiver
            Object to be kept in the foreground which reacts to messages.
        """
        connection_id = next(self._connection_ids)
        sender = MessageSender(
            connection_id=connection_id,
            signallee=self._signallee,
            message_queue=self._message_queue,
        )
        receiver = MessageReceiver()
        self._receivers[connection_id] = receiver
        return sender, receiver

    def connect(self):
        """
        Connect to the message stream.
        """
        self._signallee = _MessageSignallee()
        self._signallee.bind_to_callback(self._route_message)

    def disconnect(self):
        """
        Disconnect from the message stream.
        """
        self._signallee.unbind()
        self._signallee = None

    # Private traits ##########################################################

    #: Internal queue for messages from all senders.
    _message_queue = Any

    #: Source of new connection ids.
    _connection_ids = Instance(collections.Iterator)

    #: Receivers, keyed by connection_id.
    _receivers = Dict(Int, Any)

    #: Object receiving the "message_sent" event.
    _signallee = Instance(_MessageSignallee)

    # Private methods #########################################################

    def _route_message(self, event):
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
