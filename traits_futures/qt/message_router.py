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
Message routing for the Qt toolkit.
"""
import collections.abc
import itertools
import queue

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


class MessageSender:
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
        self.signaller = None
        self.message_queue = message_queue

    def __enter__(self):
        self.signaller = _MessageSignaller()
        self.signaller.message_sent.connect(self.signallee.message_sent)
        return self

    def __exit__(self, *exc_info):
        self.message_queue.put(("done", self.connection_id))
        self.signaller.message_sent.emit()

        self.signaller.message_sent.disconnect(self.signallee.message_sent)
        self.signaller = None

    def send(self, message):
        """
        Send a message to the router.
        """
        self.message_queue.put(("message", self.connection_id, message))
        self.signaller.message_sent.emit()


class MessageReceiver(HasStrictTraits):
    """
    Main-thread object that receives messages from a MessageSender.
    """

    #: Event fired when a message is received from the paired sender.
    message = Event(Any())


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
        pass

    def disconnect(self):
        """
        Undo any connections made by the ``connect`` call.
        """
        pass

    # Private traits ##########################################################

    #: Internal queue for messages from all senders.
    _message_queue = Any()

    #: Source of new connection ids.
    _connection_ids = Instance(collections.abc.Iterator)

    #: Receivers, keyed by connection_id.
    _receivers = Dict(Int(), Any())

    #: QObject providing slot for the "message_sent" signal.
    _signallee = Instance(_MessageSignallee)

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
            self.receiver_done = receiver

    def __message_queue_default(self):
        return queue.Queue()

    def __connection_ids_default(self):
        return itertools.count()

    def __signallee_default(self):
        return _MessageSignallee(on_message_sent=self._route_message)
