# Main-thread controller for background jobs.
from __future__ import absolute_import, print_function, unicode_literals

import collections
import itertools
import threading

import concurrent.futures

from traits.api import (
    Any, Dict, HasStrictTraits, Instance, Int, on_trait_change)

from traits_futures.message_handling import MessageReceiver, MessageSender


class TraitsExecutor(HasStrictTraits):
    """
    Executor to initiate and manage background jobs.
    """
    executor = Instance(concurrent.futures.Executor)

    _message_receiver = Instance(MessageReceiver, ())

    _current_futures = Dict(Int, Any)

    _job_ids = Instance(collections.Iterator)

    def __job_ids_default(self):
        return itertools.count()

    def submit(self, job):
        job_id = next(self._job_ids)
        message_sender = MessageSender(
            job_id=job_id,
            receiver=self._message_receiver,
        )
        future, runner = job.prepare(
            cancel_event=threading.Event(),
            message_sender=message_sender,
        )
        self._current_futures[job_id] = future
        self.executor.submit(runner)
        return future

    def run_loop(self):
        while self._current_futures:
            message = self._message_receiver.message_queue.get()
            self._process_message(message)

    def run_loop_until(self, condition):
        while not condition():
            message = self._message_receiver.message_queue.get()
            self._process_message(message)

    @on_trait_change('_message_receiver:received')
    def _process_message(self, message):
        job_id, msg = message
        job = self._current_futures[job_id]
        done = job.process_message(msg)
        if done:
            self._current_futures.pop(job_id)
