# Main-thread controller for background jobs.

import collections
import itertools
import Queue as queue

import concurrent.futures

from traits.api import Any, Dict, HasStrictTraits, Instance, Int

from traits_futures.job import Job


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
        runner = job.prepare(
            job_id=job_id,
            results_queue=self._results_queue,
        )
        self._current_jobs[job_id] = job
        self.executor.submit(runner)

    def run_loop(self):
        while self._current_jobs:
            msg = self._results_queue.get()
            self._process_message(msg)

    def run_loop_until(self, condition):
        while not condition():
            msg = self._results_queue.get()
            self._process_message(msg)

    def _process_message(self, msg):
        job_id = msg[0]
        job = self._current_jobs[job_id]
        done = job.process_message(msg[1:])
        if done:
            self._current_jobs.pop(job_id)

    def _remove_job(self, job_id):
        self._current_jobs.pop(job_id)
