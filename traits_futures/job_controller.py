# Main-thread controller for background jobs.

import collections
import itertools
import Queue as queue

import concurrent.futures

from traits.api import Any, Dict, HasStrictTraits, Instance, Int

from traits_futures.job import (
    Job,
    COMPLETED,
    EXECUTING,
    QUEUED,
)
from traits_futures.job_runner import (
    JobRunner,
    RAISED,
    RETURNED,
    STARTING,
)


class JobController(HasStrictTraits):
    executor = Instance(concurrent.futures.Executor)

    _results_queue = Any

    _current_jobs = Dict(Int, Job)

    _job_ids = Instance(collections.Iterator)

    def __results_queue_default(self):
        return queue.Queue()

    def __job_ids_default(self):
        return itertools.count()

    def submit(self, job):
        job_id = next(self._job_ids)
        runner = JobRunner(
            job=job,
            job_id=job_id,
            results_queue=self._results_queue,
        )
        self.executor.submit(runner)
        self._current_jobs[job_id] = job
        job.state = QUEUED
        return job_id

    def run_loop(self):
        while self._current_jobs:
            msg = self._results_queue.get()
            self._process_message(msg)

    def _process_message(self, msg):
        job_id, msg_type, msg_args = msg

        if msg_type == STARTING:
            job = self._current_jobs[job_id]
            job.state = EXECUTING
        elif msg_type == RAISED:
            job = self._current_jobs.pop(job_id)
            job.exception = msg_args
            job.state = COMPLETED
        elif msg_type == RETURNED:
            job = self._current_jobs.pop(job_id)
            job.result = msg_args
            job.state = COMPLETED
        else:
            raise ValueError(
                "Unrecognised message type: {!r}".format(msg_type))
