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

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc_info):
        self.stop()

    def start(self):
        """
        Do any local setup necessary, and send an initial message.
        """
        # self.message_queue.put(("start", self.connection_id))

    def stop(self):
        """
        Send a final message, then do any local teardown necessary.
        """
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
