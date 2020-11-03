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
Support for routing message streams from background processes to their
corresponding foreground receivers.

This version of the module is for a multiprocessing back end and
the null tookit (using the asyncio event loop) on the front end.
"""

import asyncio
import collections.abc
import itertools
import multiprocessing.managers
import queue
import threading

from traits.api import Any, Dict, Event, HasStrictTraits, Instance, Int

from traits_futures.null.pinger import AsyncioPinger

# Plan:

# Components are:
# - a multiprocessing queue, shared with all children
# - a local queue
# - a local thread which copies incoming messages from the multiprocessing
#   queue to the local queue, and schedules an asyncio task to process the
#   message from the local queue

# This is an exact duplicate of the Qt version. Fix the duplication!


class MessageSender:
    def __init__(self, connection_id, message_queue):
        self.connection_id = connection_id
        self.message_queue = message_queue

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.message_queue.put(("done", self.connection_id))

    def send(self, message):
        """
        Send a message to the router.

        Parameters
        ----------
        message : object
            Message to be sent to the corresponding foreground receiver.
            via the router.
        """
        self.message_queue.put(("message", self.connection_id, message))


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

    Multiprocessing variant.

    Requires the asyncio event loop to be running in order for messages
    to arrive.
    """

    #: Event fired when a receiver is dropped from the routing table.
    receiver_done = Event(Instance(MessageReceiver))

    def __init__(self, **traits):
        super(MessageProcessRouter, self).__init__(**traits)

        self._manager = multiprocessing.Manager()
        self._local_message_queue = queue.Queue()
        self._process_message_queue = self._manager.Queue()

        self._event_loop = asyncio.get_event_loop()

        self._monitor_thread = threading.Thread(
            target=monitor_queue,
            args=(
                self._process_message_queue,
                self._local_message_queue,
                self,
                self._event_loop,
            ),
        )
        # XXX Need tests for shutdown.
        self._monitor_thread.start()

    def connect(self):
        """
        Connect to the current event loop.
        """
        # XXX Move initialization here

    def disconnect(self):
        """
        Disconnect from the event loop.
        """
        self._process_message_queue.put(None)
        self._monitor_thread.join()
        # self._process_message_queue.join()
        self._manager.shutdown()
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

    #: Local queue for messages to the UI thread.
    _local_message_queue = Any()

    #: Thread transferring messages from the process queue to the local
    #: queue.
    _monitor_thread = Any()

    #: Source of new connection ids.
    _connection_ids = Instance(collections.abc.Iterator)

    #: Receivers, keyed by connection_id.
    _receivers = Dict(Int(), Any())

    #: Manager, used to create cancellation Events and message queues.
    _manager = Instance(multiprocessing.managers.BaseManager)

    #: The event loop used for message routing.
    _event_loop = Any()

    # Private methods #########################################################

    async def _route_message(self):
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


def monitor_queue(process_queue, local_queue, router, asyncio_event_loop):
    """
    Move incoming child process messages to the local queue.

    Monitors the process queue for incoming messages, and transfers
    those messages to the local queue, while also requesting that
    the event loop eventually process that message.
    """
    pinger = AsyncioPinger(asyncio_event_loop, router._route_message)
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
