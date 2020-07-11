# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

import collections.abc
import itertools
import multiprocessing.managers
import queue
import threading

from traits.api import Any, Dict, Event, HasStrictTraits, Instance, Int

# XXX Move these to a shared location.
from traits_futures.qt.message_router import (
    _MessageSignallee,
    _MessageSignaller,
)


class MessageSender:
    def __init__(self, connection_id, message_queue):
        self.connection_id = connection_id
        self.message_queue = message_queue

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        done_message = "done", self.connection_id
        self.message_queue.put(done_message)

    def send(self, message):
        wrapped_message = "message", self.connection_id, message
        self.message_queue.put(wrapped_message)

    def send_message(self, message_type, message_args=None):
        self.send((message_type, message_args))


class MessageReceiver(HasStrictTraits):
    """
    Main-thread object that receives messages from a MessageSender.
    """

    #: Event fired when a message is received from the paired sender.
    message = Event(Any())


class MessageProcessRouter(HasStrictTraits):
    """
    Router for messages, sent by means of Qt signals and slots.

    Multiprocessing variant.

    Requires the event loop to be running in order for messages to arrive.
    """

    #: Event fired when a receiver is dropped from the routing table.
    receiver_done = Event(Instance(MessageReceiver))

    def __init__(self, **traits):
        super(MessageProcessRouter, self).__init__(**traits)

        self._manager = multiprocessing.Manager()
        self._local_message_queue = queue.Queue()
        self._process_message_queue = self._manager.Queue()

        self._monitor_thread = threading.Thread(
            target=monitor_queue,
            args=(
                self._process_message_queue,
                self._local_message_queue,
                self._signallee,
            ),
        )
        # XXX Need tests for shutdown.
        self._monitor_thread.start()

    def connect(self):
        """
        Prepare router for routing.
        """
        # XXX Move initialization here.
        pass

    def disconnect(self):
        """
        Undo any connections made by the ``connect`` call.
        """
        self._process_message_queue.put(None)
        self._monitor_thread.join()
        # self._process_message_queue.join()
        self._manager.shutdown()

    #: Event fired when a receiver is dropped from the routing table.
    receiver_done = Event(Instance(MessageReceiver))

    def pipe(self):
        # XXX Docstring!
        connection_id = next(self._connection_ids)

        sender = MessageSender(
            connection_id=connection_id,
            message_queue=self._process_message_queue,
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

    def event(self):
        """
        New event, for background process cancellation.
        """
        return self._manager.Event()

    # Private traits ##########################################################

    #: Queue receiving messages from child processes.
    _process_message_queue = Any()

    #: Local queue for messages to the UI thread.
    _local_message_queue = Any()

    #: Thread transferring messages from the process queue to the local
    #: queue.
    _monitor_thread = Any()

    #: Source of new connection ids.
    _connection_ids = Instance(collections.abc.Iterator)

    #: Receivers, keyed by connection_id.
    _receivers = Dict(Int(), Any())

    #: QObject providing slot for the "message_sent" signal.
    _signallee = Instance(_MessageSignallee)

    #: Manager, used to create cancellation Events and message queues.
    _manager = Instance(multiprocessing.managers.BaseManager)

    # Private methods #########################################################

    def _route_message(self):
        wrapped_message = self._local_message_queue.get()
        if wrapped_message[0] == "message":
            _, connection_id, message = wrapped_message
            receiver = self._receivers[connection_id]
            receiver.message = message
        else:
            assert wrapped_message[0] == "done"
            _, connection_id = wrapped_message
            receiver = self._receivers.pop(connection_id)
            self.receiver_done = receiver

    def __connection_ids_default(self):
        return itertools.count()

    def __signallee_default(self):
        return _MessageSignallee(on_message_sent=self._route_message)


def monitor_queue(process_queue, local_queue, signallee):
    """
    Move incoming child process messages to the local queue.

    Monitors the process queue for incoming messages, and transfers
    those messages to the local queue, while signalling Qt that there's
    a message to process.
    """
    signaller = _MessageSignaller()
    signaller.message_sent.connect(signallee.message_sent)
    try:
        while True:
            # XXX Add a timeout?
            message = process_queue.get()
            if not isinstance(message, tuple):
                break
            local_queue.put(message)
            # Avoid hanging onto a reference to the message until the next
            # queue element arrives.
            del message
            signaller.message_sent.emit()
    finally:
        signaller.message_sent.disconnect(signallee.message_sent)
