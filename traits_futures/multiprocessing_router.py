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
import logging
import multiprocessing.managers
import queue
import threading

from traits.api import (
    Any,
    Bool,
    Dict,
    HasStrictTraits,
    Instance,
    Int,
    provides,
)

from traits_futures.i_message_router import IMessageRouter
from traits_futures.message_receiver import MessageReceiver
from traits_futures.multiprocessing_sender import MultiprocessingSender
from traits_futures.toolkit_support import toolkit

logger = logging.getLogger(__name__)

Pingee = toolkit("pinger:Pingee")
Pinger = toolkit("pinger:Pinger")


@provides(IMessageRouter)
class MultiprocessingRouter(HasStrictTraits):
    """
    Router for messages from background jobs to their corresponding futures.

    Multiprocessing variant.

    Requires the event loop to be running in order for messages to arrive.
    """

    def start(self):
        """
        Prepare router for routing.
        """
        if self._running:
            raise RuntimeError("Router is already running")

        self._manager = multiprocessing.Manager()
        self._local_message_queue = queue.Queue()
        self._process_message_queue = self._manager.Queue()

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
        self._monitor_thread.start()

        self._running = True

    def stop(self):
        """
        Undo any connections made by the ``connect`` call.
        """
        if not self._running:
            raise RuntimeError("Router is not running")

        if self._receivers:
            logger.warning("there are unclosed pipes")

        # Shut everything down in reverse order.
        # First the monitor thread.
        self._process_message_queue.put(None)
        self._monitor_thread.join()
        self._monitor_thread = None

        # No shutdown required for the process_message_queue: it's enough
        # to shut down the manager.
        self._manager.shutdown()
        self._manager = None
        self._process_message_queue = None

        self._pingee.disconnect()
        self._pingee = None

        self._local_message_queue = None

        self._running = False

    def pipe(self):
        """
        Create a (sender, receiver) pair for sending messages.

        The sender object is passed to the background task, and
        can then be used by that background task to send messages.

        The receiver has a single trait which is fired when a message is
        received from the background and routed to the receiver.

        Not thread safe. Should only ever be called from the main thread.

        Returns
        -------
        sender : IMessageSender
        receiver : IMessageReceiver
        """
        if not self._running:
            raise RuntimeError("Router is not running.")

        connection_id = next(self._connection_ids)

        sender = MultiprocessingSender(
            connection_id=connection_id,
            message_queue=self._process_message_queue,
        )
        receiver = MessageReceiver(connection_id=connection_id)
        self._receivers[connection_id] = receiver
        return sender, receiver

    def close_pipe(self, receiver):
        if not self._running:
            raise RuntimeError("Router is not running.")

        connection_id = receiver.connection_id
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

    #: Router status
    _running = Bool(False)

    # Private methods #########################################################

    def _route_message(self):
        connection_id, message = self._local_message_queue.get()
        try:
            receiver = self._receivers[connection_id]
        except KeyError:
            logger.warning(
                f"No receiver for message with connection_id {connection_id}. "
                "Message discarded."
            )
        else:
            receiver.message = message

    def __connection_ids_default(self):
        return itertools.count()


def monitor_queue(process_queue, local_queue, pingee):
    """
    Move incoming child process messages to the local queue.

    Monitors the process queue for incoming messages, and transfers
    those messages to the local queue, while also requesting that
    the event loop eventually process that message.
    """
    # XXX Inconsistency with multithreading version, where we
    # instantiate the Pinger on the main thread (and then pass
    # to the child thread)
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
