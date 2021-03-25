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

This version of the module is for a multithreading back end.
"""

import collections.abc
import itertools
import queue

from traits.api import Any, Dict, HasStrictTraits, Instance, Int

from traits_futures.i_message_router import IMessageRouter
from traits_futures.message_receiver import MessageReceiver
from traits_futures.multithreading_sender import MultithreadingSender
from traits_futures.toolkit_support import toolkit

Pingee = toolkit("pinger:Pingee")
Pinger = toolkit("pinger:Pinger")


@IMessageRouter.register
class MultithreadingRouter(HasStrictTraits):
    """
    Router for messages from a background thread.

    Requires the event loop to be running in order for messages to arrive.
    """

    def pipe(self):
        """
        Create a (sender, receiver) pair for sending messages.

        Returns
        -------
        sender : MultithreadingSender
            Object to be passed to the background task to send messages.
        receiver : MessageReceiver
            Object to be kept in the foreground which reacts to messages.
        """
        connection_id = next(self._connection_ids)
        pinger = Pinger(pingee=self._pingee)
        sender = MultithreadingSender(
            connection_id=connection_id,
            pinger=pinger,
            message_queue=self._message_queue,
        )
        receiver = MessageReceiver()
        self._receivers[connection_id] = receiver
        return sender, receiver

    def close_pipe(self, receiver):
        for connection_id, gen_receiver in self._receivers.items():
            if receiver == gen_receiver:
                break
        else:
            connection_id = None

        if connection_id is not None:
            self._receivers.pop(connection_id)

    def connect(self):
        """
        Prepare router for routing.
        """
        self._message_queue = queue.Queue()

        self._pingee = Pingee(on_ping=self._route_message)
        self._pingee.connect()

    def disconnect(self):
        """
        Undo any connections made by the ``connect`` call.
        """
        # XXX Restore me; figure out why this breaks
        # Should we warn if we disconnect while we're still listening,
        # or perhaps just not care?
        assert not self._receivers

        self._pingee.disconnect()
        self._pingee = None

        self._message_queue = None

    # Private traits ##########################################################

    #: Internal queue for messages from all senders.
    _message_queue = Any()

    #: Source of new connection ids.
    _connection_ids = Instance(collections.abc.Iterator)

    #: Receivers, keyed by connection_id.
    _receivers = Dict(Int(), Any())

    #: Receiver for the "message_sent" signal.
    _pingee = Instance(Pingee)

    # Private methods #########################################################

    def _route_message(self):
        connection_id, message = self._message_queue.get()
        receiver = self._receivers[connection_id]
        receiver.message = message

    def __connection_ids_default(self):
        return itertools.count()
