# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

import asyncio


class AsyncioPinger:
    def __init__(self, signallee):
        self.signallee = signallee

    def connect(self):
        """
        Connect to the receiver.
        """
        pass

    def disconnect(self):
        """
        Disconnect from the receiver.
        """
        pass

    def ping(self):
        """
        Send a ping to the receiver.
        """
        event_loop = self.signallee.event_loop
        event_loop.call_soon_threadsafe(self.signallee.on_message_sent)


class AsyncioPingee:
    def __init__(self, on_message_sent):
        self.event_loop = asyncio.get_event_loop()
        self.on_message_sent = on_message_sent

    def message_sent(self):
        self.on_message_sent()
