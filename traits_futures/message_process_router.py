# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Support for routing message streams from background processes to their
corresponding foreground receivers.

This version of the module is for a multiprocessing back end.
"""

import collections.abc
import itertools
import multiprocessing.managers
import queue
import threading

from traits.api import Any, Dict, Event, HasStrictTraits, Instance, Int

from traits_futures.message_receiver import MessageReceiver
from traits_futures.multiprocessing_sender import MultiprocessingSender
from traits_futures.toolkit_support import toolkit

Pingee = toolkit("pinger:Pingee")
Pinger = toolkit("pinger:Pinger")


class MessageProcessRouter(HasStrictTraits):
    """
    Router for messages from background jobs to their corresponding futures.

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

    def connect(self):
        """
        Prepare router for routing.
        """
        # XXX Move more initialization here.
        self._pingee = Pingee(on_ping=self._route_message)
        self._pingee.connect()

        self._monitor_thread = threading.Thread(
            target=monitor_queue,
            args=(
                self._process_message_queue,
                self._local_message_queue,
                self._pingee,
            ),
        )
        # XXX Need tests for shutdown.
        self._monitor_thread.start()

    def disconnect(self):
        """
        Undo any connections made by the ``connect`` call.
        """
        self._process_message_queue.put(None)
        self._monitor_thread.join()
        # self._process_message_queue.join()
        self._manager.shutdown()

        self._pingee.disconnect()
        self._pingee = None

    def pipe(self):
        # XXX Docstring!
        connection_id = next(self._connection_ids)

        sender = MultiprocessingSender(
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

    #: Receiver for the "message_sent" signal.
    _pingee = Instance(Pingee)

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


def monitor_queue(process_queue, local_queue, pingee):
    """
    Move incoming child process messages to the local queue.

    Monitors the process queue for incoming messages, and transfers
    those messages to the local queue, while also requesting that
    the event loop eventually process that message.
    """
    pinger = Pinger(pingee=pingee)
    pinger.connect()
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
            pinger.ping()
    finally:
        pinger.disconnect()