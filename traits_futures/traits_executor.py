# Main-thread controller for background tasks.
from __future__ import absolute_import, print_function, unicode_literals

import threading

import concurrent.futures

from traits.api import (
    Any, Dict, HasStrictTraits, Instance, Int, on_trait_change)

from traits_futures.message_handling import QtMessageReceiver


class TraitsExecutor(HasStrictTraits):
    """
    Executor to initiate and manage background tasks.
    """
    #: Executor instance backing this object.
    executor = Instance(concurrent.futures.Executor)

    #: Endpoint for receiving messages.
    _message_receiver = Any

    #: Currently executing futures, keyed by their sender_id.
    _current_futures = Dict(Int, Any)

    def submit(self, task):
        sender_id, message_sender = self._message_receiver.sender()
        future, runner = task.prepare(
            cancel_event=threading.Event(),
            message_sender=message_sender,
        )
        self._current_futures[sender_id] = future
        self.executor.submit(runner)
        return future

    @on_trait_change('_message_receiver:received')
    def _process_message(self, message):
        sender_id, msg = message
        future = self._current_futures[sender_id]
        done = future.process_message(msg)
        if done:
            self._current_futures.pop(sender_id)

    def __message_receiver_default(self):
        return QtMessageReceiver()
