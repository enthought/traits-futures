# Main-thread controller for background jobs.

import collections
import itertools
import Queue as queue
import threading

import concurrent.futures

from traits.api import Any, Dict, HasStrictTraits, Instance, Int
from traits.trait_notifiers import ui_dispatch

from traits_futures.job import Job


class QueueWithCallback(object):
    """
    Wrapper around a regular queue that fires a user-supplied callback exactly
    once for each item placed on the queue.
    """
    def __init__(self, queue, callback):
        # Underlying queue. May be any object that supports the get / put API
        # of queue.Queue. This trait should be supplied at creation time.
        self.queue = queue

        # Callback that gets called (with no arguments) every time something is
        # added to the underlying queue. This is used for example to alert the
        # UI mainloop that it needs to check the queue at some point in the
        # future.
        self.callback = callback

    def put(self, item, block=True, timeout=None):
        """
        Put an item into the queue.
        """
        self.queue.put(item, block=block, timeout=timeout)
        self.callback()

    def get(self, block=True, timeout=None):
        """
        Remove and return an item from the queue.
        """
        return self.queue.get(block=block, timeout=timeout)


class JobController(HasStrictTraits):
    executor = Instance(concurrent.futures.Executor)

    _results_queue = Any

    _current_jobs = Dict(Int, Job)

    _job_ids = Instance(collections.Iterator)

    def __results_queue_default(self):
        # The default message queue ties into a running TraitsUI session.
        return QueueWithCallback(
            queue=queue.Queue(),
            callback=lambda: ui_dispatch(self._process_message),
        )

    def __job_ids_default(self):
        return itertools.count()

    def submit(self, job):
        job_id = next(self._job_ids)
        runner = job.prepare(
            job_id=job_id,
            cancel_event=threading.Event(),
            results_queue=self._results_queue,
        )
        self._current_jobs[job_id] = job
        self.executor.submit(runner)

    def run_loop(self):
        while self._current_jobs:
            self._process_message()

    def run_loop_until(self, condition):
        while not condition():
            self._process_message()

    def _process_message(self):
        msg = self._results_queue.get()
        job_id = msg[0]
        job = self._current_jobs[job_id]
        done = job.process_message(msg[1:])
        if done:
            self._current_jobs.pop(job_id)
