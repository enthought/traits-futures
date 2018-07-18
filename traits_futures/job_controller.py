# Main-thread controller for background jobs.

import collections
import itertools
import threading

import concurrent.futures
from six.moves import queue

from pyface.qt.QtCore import QObject, Slot, Signal
from traits.api import Any, Dict, HasStrictTraits, Instance, Int


class Signaller(QObject):
    fired = Signal()


class Responder(QObject):
    def __init__(self, controller):
        QObject.__init__(self)
        self.controller = controller

    @Slot()
    def respond(self, *args, **kwargs):
        self.controller._process_message()


class WorkerQueue(object):
    """
    Represents the worker end of the main thread's message queue. Despite
    the name, this can't really be regarded as a queue any more. But
    it _does_ have a put method, which is all the worker needs.
    """
    def __init__(self, queue, responder):
        self.message_queue = queue
        self.responder = responder
        self.signaller = None

    def put(self, item):
        # Initialize the Signaller lazily, because we want to make sure
        # to create it on the worker thread. (XXX Test what happens
        # if we create it on the main thread. It may not matter.)
        if self.signaller is None:
            self.signaller = Signaller()
            # XXX We should probably do the corresponding disconnect at some
            # point.
            self.signaller.fired.connect(self.responder.respond)

        self.message_queue.put(item)
        self.signaller.fired.emit()


class JobController(HasStrictTraits):
    executor = Instance(concurrent.futures.Executor)

    _results_queue = Any

    _current_jobs = Dict(Int, Any)

    _job_ids = Instance(collections.Iterator)

    _responder = Instance(Responder)

    def __responder_default(self):
        # XXX Circular reference!
        return Responder(self)

    def __results_queue_default(self):
        # The default message queue ties into a running TraitsUI session.
        return queue.Queue()

    def __job_ids_default(self):
        return itertools.count()

    def submit(self, job):
        job_id = next(self._job_ids)
        worker_queue = WorkerQueue(self._results_queue, self._responder)
        job_handle, runner = job.prepare(
            job_id=job_id,
            cancel_event=threading.Event(),
            results_queue=worker_queue,
        )
        self._current_jobs[job_id] = job_handle
        self.executor.submit(runner)
        return job_handle

    def run_loop(self):
        while self._current_jobs:
            self._process_message()

    def run_loop_until(self, condition):
        while not condition():
            self._process_message()

    def _process_message(self):
        job_id, msg = self._results_queue.get()
        job = self._current_jobs[job_id]
        done = job.process_message(msg)
        if done:
            self._current_jobs.pop(job_id)
