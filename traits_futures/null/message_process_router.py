# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Support for routing message streams from background processes to their
corresponding foreground receivers.
"""

import collections.abc
import itertools
import multiprocessing
import threading

from traits.api import Any, Dict, Event, HasStrictTraits, Instance, Int

from traits_futures.null.package_globals import get_event_loop


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


# XXX Fix the repetition! MessageReceiver is the same regardless of
# parallelism and toolkit.


class MessageReceiver(HasStrictTraits):
    """
    Main-thread object that receives messages from a MessageSender.
    """

    #: Event fired when a message is received from the paired sender.
    message = Event(Any())


class MessageProcessRouter(HasStrictTraits):
    """
    Router for messages from background jobs to their corresponding futures.
    """

    #: Event fired when a receiver is dropped from the routing table.
    receiver_done = Event(Instance(MessageReceiver))

    def connect(self):
        """
        Connect to the current event loop.
        """
        self._event_loop = get_event_loop()
        self._signallee = self._event_loop.async_caller(self._route_message)
        self._manager = multiprocessing.Manager()
        self._process_message_queue = self._manager.Queue()
        self._monitor_thread = threading.Thread(
            target=monitor_queue,
            args=(
                self._process_message_queue,
                self._event_loop,
                self._signallee,
            ),
        )
        self._monitor_thread.start()

    def disconnect(self):
        """
        Disconnect from the event loop.
        """
        self._process_message_queue.put(None)
        self._monitor_thread.join()
        # self._process_message_queue.join()
        self._manager.shutdown()
        self._signallee.close()
        self._event_loop = None

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
        Discard an unused sender / receiver pair.
        """
        connection_id = sender.connection_id
        self._receivers.pop(connection_id)

    # Private traits ##########################################################

    #: Queue receiving messages from child processes.
    _process_message_queue = Any()

    #: The event loop used for message routing.
    _event_loop = Any()

    #: Thread transferring messages from the process queue to the local
    #: queue.
    _monitor_thread = Any()

    #: Source of new connection ids.
    _connection_ids = Instance(collections.abc.Iterator)

    #: Receivers, keyed by connection_id.
    _receivers = Dict(Int(), Any())

    #: Object called to place a process-message action on the event queue.
    _signallee = Any()

    #: Manager, used to create cancellation Events and message queues.
    _manager = Instance(multiprocessing.managers.BaseManager)

    # Private methods #########################################################

    def _route_message(self, wrapped_message):
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


def monitor_queue(process_queue, event_loop, route_message):
    """
    Move incoming child process messages to the event loop.
    """
    while True:
        message = process_queue.get()
        if not isinstance(message, tuple):
            break
        route_message(message)
        # Avoid hanging onto a reference to the message until the next
        # queue element arrives.
        del message
