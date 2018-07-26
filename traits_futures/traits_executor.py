# Main-thread controller for background tasks.
from __future__ import absolute_import, print_function, unicode_literals

import threading

import concurrent.futures

from traits.api import Any, HasStrictTraits, Instance

from traits_futures.message_handling import QtMessageRouter


class TraitsExecutor(HasStrictTraits):
    """
    Executor to initiate and manage background tasks.
    """
    #: Executor instance backing this object.
    executor = Instance(concurrent.futures.Executor)

    #: Endpoint for receiving messages.
    _message_router = Any

    def submit(self, task):
        sender_id, sender, receiver = self._message_router.sender()
        future, runner = task.prepare(
            cancel_event=threading.Event(),
            message_sender=sender,
            message_receiver=receiver,
        )
        self.executor.submit(runner)
        return future

    def __message_router_default(self):
        return QtMessageRouter()
