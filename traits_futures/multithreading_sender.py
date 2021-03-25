# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

from traits_futures.i_message_sender import IMessageSender


#: Internal states. The sender starts in the INITIAL state, moves to
#: the OPEN state when 'start' is called, and from OPEN to CLOSED when
#: 'stop' is called. Messages can only be sent while the sending is in
#: OPEN state.
_INITIAL = "initial"
_OPEN = "open"
_CLOSED = "closed"


@IMessageSender.register
class MultithreadingSender:
    """
    Object allowing the worker to send messages.

    This class will be instantiated in the main thread, but passed to the
    worker thread to allow the worker to communicate back to the main
    thread.

    Only the worker thread should use the send method, and only
    inside a "with sender:" block.
    """

    def __init__(self, connection_id, pinger, message_queue):
        self.connection_id = connection_id
        self.pinger = pinger
        self.message_queue = message_queue
        self._state = _INITIAL

    def start(self):
        """
        Do any local setup necessary, and send an initial message.
        """
        if self._state != _INITIAL:
            raise RuntimeError(
                f"Sender already started: state is {self._state}"
            )

        self.pinger.connect()

        self._state = _OPEN

    def stop(self):
        """
        Do any teardown, and send a final message.
        """
        if self._state != _OPEN:
            raise RuntimeError(
                "Sender not started, or already stopped: "
                f"state is {self._state}"
            )

        self.pinger.disconnect()

        self._state = _CLOSED

    def send(self, message):
        """
        Send a message to the router.
        """
        if self._state != _OPEN:
            raise RuntimeError(
                "Sender must be in OPEN state to send messages: "
                f"state is {self._state}"
            )

        self.message_queue.put(("message", self.connection_id, message))
        self.pinger.ping()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc_info):
        self.stop()
