# (C) Copyright 2018-2023 Enthought, Inc., Austin, TX
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
interfaces for tasks executed on a background thread.
"""

import collections.abc
import itertools
import logging
import queue
import time

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

from traits_futures.i_event_loop import IEventLoop
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
class MultithreadingSender:
    """
    Object allowing the worker to send messages.

    This class will be instantiated in the main thread, and the instance passed
    to the worker thread to allow the worker to communicate back to the main
    thread.

    Parameters
    ----------
    connection_id : int
        Id of the matching receiver; used for message routing.
    pingee : IPingee
        Recipient for pings, used to notify the event loop that there's
        a message pending.
    message_queue : queue.Queue
        Thread-safe queue for passing messages to the foreground.
    """

    def __init__(self, connection_id, pingee, message_queue):
        self.connection_id = connection_id
        self.pingee = pingee
        self.message_queue = message_queue
        self._state = _INITIAL
        self.pinger = None

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

        self.pinger = self.pingee.pinger()
        self.pinger.connect()

        self._state = _OPEN

    def send(self, message):
        """
        Send a message to the router.

        Not thread-safe. The 'start', 'send' and 'stop' methods should
        all be called from the same thread.

        Parameters
        ----------
        message : object
            Typically this will be immutable, small, and pickleable.

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
        self.pinger.ping()

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

        self.pinger.disconnect()
        self.pinger = None

        self._state = _CLOSED

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc_info):
        self.stop()


@provides(IMessageReceiver)
class MultithreadingReceiver(HasStrictTraits):
    """
    Implementation of the IMessageReceiver interface for the case where the
    sender will be in a background thread.
    """

    #: Event fired when a message is received from the paired sender.
    message = Event(Any())

    #: Connection id, matching that of the paired sender.
    connection_id = Int()


@provides(IMessageRouter)
class MultithreadingRouter(HasRequiredTraits):
    """
    Implementation of the IMessageRouter interface for the case where the
    sender will be in a background thread.

    Parameters
    ----------
    event_loop : IEventLoop
        The event loop used to trigger message dispatch.

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
            raise RuntimeError("router is already running")

        self._message_queue = queue.Queue()
        self._link_to_event_loop()

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
            raise RuntimeError("router is not running")

        if self._receivers:
            logger.warning(f"{self} has {len(self._receivers)} unclosed pipes")

        self._unlink_from_event_loop()

        self._message_queue = None

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
        sender : MultithreadingSender
            Object to be passed to the background task.
        receiver : MultithreadingReceiver
            Object kept in the foreground, which reacts to messages.

        Raises
        ------
        RuntimeError
            If the router is not currently running.
        """
        if not self._running:
            raise RuntimeError("router is not running")

        connection_id = next(self._connection_ids)
        sender = MultithreadingSender(
            connection_id=connection_id,
            pingee=self._pingee,
            message_queue=self._message_queue,
        )
        receiver = MultithreadingReceiver(connection_id=connection_id)
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
        receiver : MultithreadingReceiver
            Receiver half of the pair returned by the ``pipe`` method.

        Raises
        ------
        RuntimeError
            If the router is not currently running.
        """
        if not self._running:
            raise RuntimeError("router is not running")

        connection_id = receiver.connection_id
        self._receivers.pop(connection_id)
        logger.debug(
            f"{self} closed pipe #{connection_id} with receiver {receiver}"
        )

    def route_until(self, condition, timeout=None):
        """
        Manually drive the router until a given condition occurs, or timeout.

        This is primarily used as part of a clean shutdown.

        Note: this has the side-effect of moving the router from "event loop"
        mode to "manual" mode. This mode switch is permanent, in the sense that
        after this point, the router will no longer respond to pings: any
        messages will need to be processed through this function.

        Parameters
        ----------
        condition
            Zero-argument callable returning a boolean. When this condition
            becomes true, this method will stop routing messages. If the
            condition is already true on entry, no messages will be routed.
        timeout : float, optional
            Maximum number of seconds to route messages for.

        Raises
        ------
        RuntimeError
            If the condition did not become true before timeout.
        """
        self._unlink_from_event_loop()

        if timeout is None:
            while not condition():
                self._route_message(block=True)
        else:
            end_time = time.monotonic() + timeout
            while not condition():
                try:
                    time_remaining = end_time - time.monotonic()
                    self._route_message(block=True, timeout=time_remaining)
                except queue.Empty:
                    raise RuntimeError("Timed out waiting for messages")

    # Public traits ###########################################################

    #: The event loop used to trigger message dispatch.
    event_loop = Instance(IEventLoop, required=True)

    # Private traits ##########################################################

    #: Internal queue for messages from all senders.
    _message_queue = Instance(queue.Queue)

    #: Source of new connection ids.
    _connection_ids = Instance(collections.abc.Iterator)

    #: Receivers, keyed by connection_id.
    _receivers = Dict(Int(), Instance(MultithreadingReceiver))

    #: Receiver for the "message_sent" signal.
    _pingee = Instance(IPingee)

    #: Bool keeping track of whether we're linked to the event loop
    #: or not.
    _linked = Bool(False)

    #: Router status: True if running, False if stopped.
    _running = Bool(False)

    # Private methods #########################################################

    def _link_to_event_loop(self):
        """
        Link this router to the event loop.
        """
        if self._linked:
            # Raise, because lifetime management of self._pingee is delicate,
            # so if we ever get here then something likely needs fixing.
            raise RuntimeError("Already linked to the event loop")

        self._pingee = self.event_loop.pingee(on_ping=self._route_message)
        self._pingee.connect()
        self._linked = True

    def _unlink_from_event_loop(self):
        """
        Unlink this router from the event loop, if it's linked.

        After this call, the router will no longer react to any pending
        tasks on the event loop.
        """
        if self._linked:
            # Note: it might be tempting to set self._pingee to None at this
            # point, and to use the None-ness (or not) of self._pingee to avoid
            # needing self._linked. But it's important not to do so: we need to
            # be sure that the main thread reference to the Pingee outlives any
            # reference on background threads. Otherwise we end up collection a
            # Qt object (the Pingee) on a thread other than the one it was
            # created on, and that's unsafe in general.
            self._pingee.disconnect()
            self._linked = False

    def _route_message(self, *, block=False, timeout=None):
        """
        Get and dispatch a message from the local message queue.

        Parameters
        ----------
        block : bool, optional
            If True, block until either a message arrives or until timeout. If
            False (the default), we expect a message to already be present in
            the queue.
        timeout : float, optional
            Maximum time to wait for a message to arrive. If no timeout
            is given and ``block`` is True, wait indefinitely. If ``block``
            is False, this parameter is ignored.

        Raises
        ------
        queue.Empty
            If no message arrives within the given timeout.
        """
        connection_id, message = self._message_queue.get(
            block=block,
            timeout=None if timeout is None else max(timeout, 0.0),
        )
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
