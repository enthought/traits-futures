from __future__ import absolute_import, print_function, unicode_literals

from six.moves import queue

from pyface.qt.QtCore import QObject, Signal, Slot
from traits.api import Any, Event, HasStrictTraits, Instance


class MessageSender(object):
    """
    Object allowing the worker to send messages.

    This class will be instantiated in the main thread, but passed to
    the worker thread to allow it to communicate. Only the worker thread
    should call the connect, disconnect and send methods.
    """
    def __init__(self, receiver, task_id):
        self.message_queue = receiver.message_queue
        self.receiver = receiver.signal_receiver
        self.task_id = task_id
        self.message_indicator = None

    def connect(self):
        self.message_indicator = MessageIndicator()
        self.message_indicator.message_sent.connect(self.receiver.respond)

    def disconnect(self):
        self.message_indicator.message_sent.disconnect(self.receiver.respond)
        self.message_indicator = None

    def send(self, message):
        self.message_queue.put((self.task_id, message))
        self.message_indicator.message_sent.emit()


class MessageIndicator(QObject):
    """
    Object used by the background thread to signal to the UI that
    a message has been queued.

    This class will be instantiated in the worker thread, once per background
    task.
    """
    message_sent = Signal()


class MessageSignalReceiver(QObject):
    """
    Object that listens for the 'message_sent' signal.

    This object stays in the main thread.
    """
    def __init__(self, callback):
        QObject.__init__(self)
        self.callback = callback

    @Slot()
    def respond(self):
        self.callback()


class MessageReceiver(HasStrictTraits):
    """
    Main-thread object that receives messages from background threads.
    """
    # Event fired whenever a message is received.
    received = Event(Any)

    message_queue = Any

    signal_receiver = Instance(MessageSignalReceiver)

    def _message_queue_default(self):
        return queue.Queue()

    def _signal_receiver_default(self):
        return MessageSignalReceiver(callback=self._read_message)

    def _read_message(self):
        self.received = self.message_queue.get()
