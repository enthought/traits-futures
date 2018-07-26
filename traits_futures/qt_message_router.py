from __future__ import absolute_import, print_function, unicode_literals

import collections
import itertools

from six.moves import queue

from pyface.qt.QtCore import QObject, Signal, Slot
from traits.api import Any, Dict, Event, HasStrictTraits, Instance, Int


class _MessageSignaller(QObject):
    """
    QObject used to tell the UI that a message is queued.

    This class must be instantiated in the worker thread.
    """
    message_sent = Signal()


class _MessageSignallee(QObject):
    """
    QObject providing a slot for the "message_sent" signal to connect to.

    This object stays in the main thread.
    """
    def __init__(self, on_message_sent):
        QObject.__init__(self)
        self.on_message_sent = on_message_sent

    @Slot()
    def message_sent(self):
        self.on_message_sent()


class QtMessageSender(object):
    """
    Object allowing the worker to send messages.

    This class will be instantiated in the main thread, but passed to the
    worker thread to allow the worker to communicate back to the main
    thread.

    Only the worker thread should use the send method, and only
    inside a "with sender:" block.
    """
    def __init__(self, sender_id, signallee, message_queue):
        self.sender_id = sender_id
        self.signallee = signallee
        self.signaller = None
        self.message_queue = message_queue

    def __enter__(self):
        self.signaller = _MessageSignaller()
        self.signaller.message_sent.connect(self.signallee.message_sent)
        return self

    def __exit__(self, *exc_info):
        self.message_queue.put(("done", self.sender_id))
        self.signaller.message_sent.emit()

        self.signaller.message_sent.disconnect(self.signallee.message_sent)
        self.signaller = None

    def send(self, message):
        """
        Send a message to the router.
        """
        self.message_queue.put(("message", self.sender_id, message))
        self.signaller.message_sent.emit()


class QtMessageReceiver(HasStrictTraits):
    """
    Main-thread object that receives messages from a QtMessageSender.
    """
    #: Event fired when a message is received from the paired sender.
    message = Event(Any)


class QtMessageRouter(HasStrictTraits):
    """
    Router for messages, sent by means of Qt signals and slots.

    Requires the event loop to be running in order for messages to arrive.
    """
    #: Internal queue for messages from all senders.
    _message_queue = Any

    #: Source of task ids for new tasks.
    _sender_ids = Instance(collections.Iterator)

    #: Receivers, keyed by sender_id.
    _receivers = Dict(Int, Any)

    #: QObject providing slot for the "message_sent" signal.
    _signallee = Instance(_MessageSignallee)

    def __message_queue_default(self):
        return queue.Queue()

    def __sender_ids_default(self):
        return itertools.count()

    def __signallee_default(self):
        return _MessageSignallee(on_message_sent=self._read_message)

    def sender(self):
        """
        Create a new QtMessageSender for this router.
        """
        sender_id = next(self._sender_ids)
        sender = QtMessageSender(
            sender_id=sender_id,
            signallee=self._signallee,
            message_queue=self._message_queue,
        )
        receiver = QtMessageReceiver()
        self._receivers[sender_id] = receiver
        return sender, receiver

    def _read_message(self):
        wrapped_message = self._message_queue.get()
        if wrapped_message[0] == "message":
            _, sender_id, message = wrapped_message
            receiver = self._receivers[sender_id]
            receiver.message = message
        else:
            assert wrapped_message[0] == "done"
            _, sender_id = wrapped_message
            del self._receivers[sender_id]
