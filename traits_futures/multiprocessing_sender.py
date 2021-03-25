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
class MultiprocessingSender:
    """
    Object allowing the worker to send messages.

    Only the worker process should use the send method, and only inside
    a "with sender:" block.
    """

    def __init__(self, connection_id, message_queue):
        self.connection_id = connection_id
        self.message_queue = message_queue
        self._state = _INITIAL

    def start(self):
        """
        Do any local setup necessary.
        """
        if self._state != _INITIAL:
            raise RuntimeError(
                f"Sender already started: state is {self._state}"
            )

        self._state = _OPEN

    def stop(self):
        """
        Undo any setup performed in the start method.
        """
        if self._state != _OPEN:
            raise RuntimeError(
                "Sender not started, or already stopped: "
                f"state is {self._state}"
            )

        self._state = _CLOSED

    def send(self, message):
        """
        Send a message to the router.

        Parameters
        ----------
        message : object
            Message to be sent to the corresponding foreground receiver.
            via the router.
        """
        if self._state != _OPEN:
            raise RuntimeError(
                "Sender must be in OPEN state to send messages: "
                f"state is {self._state}"
            )

        self.message_queue.put(("message", self.connection_id, message))

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc_info):
        self.stop()
