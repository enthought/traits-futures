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
Implementations of the IMessageSender, IMessageReceiver and IMessageRouter
interfaces for tasks executed in a background process.

Overview of the implementation
------------------------------

When the router is started (via the ``start`` method), it sets up the
following machinery:

- A process-safe process message queue that's shared between processes
  (:attr:`MultiprocessingRouter._process_message_queue`). This queue runs in
  its own manager server process (the manager is
  :attr:`MultiprocessingRouter.manager`), and the main process and worker
  processes use proxy objects to communicate with the queue.
- A thread-safe local message queue
  (:attr:`MultiprocessingRouter._local_message_queue`) in the main process.
- A long-running thread (:attr:`MultiprocessingRouter._monitor_thread`),
  running in the main process, that continually monitors the process message
  queue and immediately transfers any messages that arrive to the local message
  queue.
- A :class:`IPingee` instance that's pinged by the monitor thread whenever a
  message is transferred from the process message queue to the local message
  queue, alerting the GUI that there's a message to process and route.

When a worker process uses the sender to send a message, the following steps
occur:

- the sender places the message onto the process message queue (using its
  local proxy for that message queue)
- the monitor thread receives the message (using *its* local proxy for the
  process message queue) and places the message onto the local message queue.
  It also pings the pingee.
- assuming a running GUI event loop, the pingee receives the ping and executes
  the :meth:`MultiprocessingRouter._route_message` callback
- the ``_route_message`` callback pulls the next message from the local message
  queue, inspects it to determine which receiver it should be sent to, and
  sends it to that receiver

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
    Event,
    HasRequiredTraits,
    HasStrictTraits,
    Instance,
    Int,
    provides,
)

from traits_futures.i_gui_context import IEventLoop
from traits_futures.i_message_router import (
    IMessageReceiver,
    IMessageRouter,
    IMessageSender,
)
from traits_futures.i_pingee import IPingee

logger = logging.getLogger(__name__)


#: Internal states for the sender. The sender starts in the _INITIAL state,
#: moves to the _OPEN state when 'start' is called, and from _OPEN to _CLOSED
#: when 'stop' is called. Messages can only be sent with the 'send' method
#: while the sender is in _OPEN state.
_INITIAL = "initial"
_OPEN = "open"
_CLOSED = "closed"


@IMessageSender.register
class MultiprocessingSender:
    """
    Object allowing the worker to send messages.

    This class will be instantiated in the main thread, and the instance passed
    to the worker process to allow the worker to communicate back to the main
    thread.

    Parameters
    ----------
    connection_id : int
        Id of the matching receiver; used for message routing.
    message_queue : multiprocessing.Queue
        Process-safe queue for passing messages to the foreground.
    """

    def __init__(self, connection_id, message_queue):
        self.connection_id = connection_id
        self.message_queue = message_queue
        self._state = _INITIAL

    def start(self):
        """
        Do any setup necessary to prepare for sending messages.

        This method must be called before any messages can be sent
        using the ``send`` method.

        Not thread-safe. The 'start', 'send' and 'stop' methods should
        all be called from the same thread.

        Raises
        ------
        RuntimeError
            If the sender has previously been started.
        """
        if self._state != _INITIAL:
            raise RuntimeError(
                f"Sender already started: state is {self._state}"
            )

        self._state = _OPEN

    def send(self, message):
        """
        Send a message to the router.

        Parameters
        ----------
        message : object
            Typically this will be immutable, small, and pickleable.

        Not thread-safe. The 'start', 'send' and 'stop' methods should
        all be called from the same thread.

        Raises
        ------
        RuntimeError
            If the sender has not been started, or has already been stopped.
        """
        if self._state != _OPEN:
            raise RuntimeError(
                "Sender must be in OPEN state to send messages: "
                f"state is {self._state}"
            )

        self.message_queue.put((self.connection_id, message))

    def stop(self):
        """
        Do any teardown.

        After this method has been called, no more messages can be sent.

        Not thread-safe. The 'start', 'send' and 'stop' methods should
        all be called from the same thread.

        Raises
        ------
        RuntimeError
            If the sender has not been started, or has already been stopped.
        """
        if self._state != _OPEN:
            raise RuntimeError(
                "Sender not started, or already stopped: "
                f"state is {self._state}"
            )

        self._state = _CLOSED

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc_info):
        self.stop()


@provides(IMessageReceiver)
class MultiprocessingReceiver(HasStrictTraits):
    """
    Implementation of the IMessageReceiver interface for the case where the
    sender will be in a background process.
    """

    #: Event fired when a message is received from the paired sender.
    message = Event(Any())

    #: Connection id, matching that of the paired sender.
    connection_id = Int()


@provides(IMessageRouter)
class MultiprocessingRouter(HasRequiredTraits):
    """
    Implementation of the IMessageRouter interface for the case where the
    sender will be in a background process.

    Parameters
    ----------
    event_loop : IEventLoop
        GUI context to use for interactions with the GUI event loop.
    manager : multiprocessing.Manager
        Manager to be used for creating the shared-process queue.
    """

    def start(self):
        """
        Start routing messages.

        This method must be called before any call to ``pipe`` or
        ``close_pipe`` can be made.

        Not thread-safe. Must always be called in the main thread.

        Raises
        ------
        RuntimeError
            If the router has already been started.
        """
        if self._running:
            raise RuntimeError("Router is already running")

        self._local_message_queue = queue.Queue()
        self._process_message_queue = self.manager.Queue()

        self._pingee = self.event_loop.pingee(on_ping=self._route_message)
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
        logger.debug(f"{self} started")

    def stop(self):
        """
        Stop routing messages.

        This method should be called in the main thread after all pipes
        are finished with. Calls to ``pipe`` or ``close_pipe`` are
        not permitted after this method has been called.

        Logs a warning if there are unclosed pipes.

        Not thread safe. Must always be called in the main thread.

        Raises
        ------
        RuntimeError
            If the router is not running.
        """
        if not self._running:
            raise RuntimeError("Router is not running")

        if self._receivers:
            logger.warning(f"{self} has {len(self._receivers)} unclosed pipes")

        # Shut everything down in reverse order.
        # First the monitor thread.
        self._process_message_queue.put(None)
        self._monitor_thread.join()
        self._monitor_thread = None

        # No shutdown required for the process_message_queue: it'll be shut
        # down when the manager is shut down. That's the responsibility of
        # whoever provided that manager. Here we just remove the local
        # reference.
        self._process_message_queue = None

        self._pingee.disconnect()
        self._pingee = None

        self._local_message_queue = None

        self._running = False
        logger.debug(f"{self} stopped")

    def pipe(self):
        """
        Create a (sender, receiver) pair for sending and receiving messages.

        The sender will be passed to the background task and used to send
        messages, while the receiver remains in the foreground.

        Not thread safe. Must always be called in the main thread.

        Returns
        -------
        sender : MultiprocessingSender
            Object to be passed to the background task.
        receiver : MultiprocessingReceiver
            Object kept in the foreground, which reacts to messages.

        Raises
        ------
        RuntimeError
            If the router is not currently running.
        """
        if not self._running:
            raise RuntimeError("Router is not running.")

        connection_id = next(self._connection_ids)

        sender = MultiprocessingSender(
            connection_id=connection_id,
            message_queue=self._process_message_queue,
        )
        receiver = MultiprocessingReceiver(connection_id=connection_id)
        self._receivers[connection_id] = receiver
        logger.debug(
            f"{self} created pipe #{connection_id} with receiver {receiver}"
        )
        return sender, receiver

    def close_pipe(self, receiver):
        """
        Close the receiver end of a pipe produced by ``pipe``.

        Removes the receiver from the routing table, so that no new messages
        can reach that receiver.

        Not thread safe. Must always be called in the main thread.

        Parameters
        ----------
        receiver : MultiprocessingReceiver
            Receiver half of the pair returned by the ``pipe`` method.

        Raises
        ------
        RuntimeError
            If the router is not currently running.
        """
        if not self._running:
            raise RuntimeError("Router is not running.")

        connection_id = receiver.connection_id
        self._receivers.pop(connection_id)
        logger.debug(
            f"{self} closed pipe #{connection_id} with receiver {receiver}"
        )

    # Public traits ###########################################################

    #: GUI context to use for interactions with the GUI event loop.
    event_loop = Instance(IEventLoop, required=True)

    #: Manager, used to create message queues.
    manager = Instance(multiprocessing.managers.BaseManager, required=True)

    # Private traits ##########################################################

    #: Queue receiving messages from child processes.
    _process_message_queue = Any()

    #: Local queue for messages to the UI thread.
    _local_message_queue = Instance(queue.Queue)

    #: Thread transferring messages from the process queue to the local queue.
    _monitor_thread = Any()

    #: Source of new connection ids.
    _connection_ids = Instance(collections.abc.Iterator)

    #: Receivers, keyed by connection_id.
    _receivers = Dict(Int(), Instance(MultiprocessingReceiver))

    #: Receiver for the "message_sent" signal.
    _pingee = Instance(IPingee)

    #: Router status: True if running, False if stopped.
    _running = Bool(False)

    # Private methods #########################################################

    def _route_message(self):
        connection_id, message = self._local_message_queue.get()
        try:
            receiver = self._receivers[connection_id]
        except KeyError:
            logger.warning(
                f"{self} discarding message from closed pipe #{connection_id}."
            )
        else:
            receiver.message = message

    def __connection_ids_default(self):
        return itertools.count()


def monitor_queue(process_queue, local_queue, pingee):
    """
    Move incoming child process messages to the local queue.

    Monitors the process queue for incoming messages, and transfers
    those messages to the local queue. For each message transferred,
    pings the event loop using the pingee to notify it that there's
    a message to be processed.

    To stop the thread, put ``None`` onto the process_queue.

    Parameters
    ----------
    process_queue : multiprocessing.Queue
        Queue to listen to for messages.
    local_queue : queue.Queue
        Queue to transfer those messages to.
    pingee : IPingee
        Recipient for pings, used to notify the GUI thread that there's
        a message pending.

    """
    pinger = pingee.pinger()
    pinger.connect()
    try:
        while True:
            try:
                message = process_queue.get(block=True, timeout=1.0)
            except queue.Empty:
                continue
            if message is None:
                break
            local_queue.put(message)
            # Avoid hanging onto a reference to the message until the next
            # queue element arrives.
            del message
            pinger.ping()
    finally:
        pinger.disconnect()
