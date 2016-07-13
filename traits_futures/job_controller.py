# Main-thread controller for background jobs.

import collections
import itertools
import Queue as queue

import concurrent.futures

from traits.api import Any, Dict, HasStrictTraits, Instance, Int

from traits_futures.job import (
    Job,
    CANCELLING,
    COMPLETED,
    EXECUTING,
    QUEUED,
)
from traits_futures.job_runner import (
    JobRunner,
    INTERRUPTED,
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

    def run_loop_until(self, condition):
        while not condition():
            msg = self._results_queue.get()
            self._process_message(msg)

    def _process_message(self, msg):
        job_id, msg_type, msg_args = msg
        job = self._current_jobs[job_id]
        if msg_type == STARTING:
            assert job.state in (QUEUED, CANCELLING)
            if job.state == QUEUED:
                job.state = EXECUTING
        elif msg_type == RETURNED:
            assert job.state in (EXECUTING, CANCELLING)
            if job.state == EXECUTING:
                job.result = msg_args
            self._remove_job(job_id)
        elif msg_type == RAISED:
            assert job.state in (EXECUTING, CANCELLING)
            if job.state == EXECUTING:
                job.exception = msg_args
            self._remove_job(job_id)
        elif msg_type == INTERRUPTED:
            assert job.state == CANCELLING
            self._remove_job(job_id)
        else:
            raise ValueError(
                "Unrecognised message type: {!r}".format(msg_type))

    def _remove_job(self, job_id):
        job = self._current_jobs[job_id]
        job.state = COMPLETED
        self._current_jobs.pop(job_id)
