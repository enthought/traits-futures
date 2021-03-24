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

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc_info):
        self.stop()

    def start(self):
        """
        Do any setup, and send an initial message.
        """
        self.pinger.connect()

        # self.message_queue.put(("start", self.connection_id))
        # self.pinger.ping()

    def stop(self):
        """
        Do any teardown, and send a final message.
        """
        self.message_queue.put(("done", self.connection_id))
        self.pinger.ping()

        self.pinger.disconnect()
        self.pinger = None

    def send(self, message):
        """
        Send a message to the router.
        """
        self.message_queue.put(("message", self.connection_id, message))
        self.pinger.ping()
