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
    def __init__(self, asyncio_event_loop, route_message):
        self.asyncio_event_loop = asyncio_event_loop
        self.route_message = route_message
        pass

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
        asyncio.run_coroutine_threadsafe(
            self.route_message(), self.asyncio_event_loop
        )
