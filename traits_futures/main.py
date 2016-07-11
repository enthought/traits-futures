import random
import time

import concurrent.futures

from traits_futures.job import Job
from traits_futures.job_controller import (
    JobController,
)


def slow_square(n):
    sleep_time = random.expovariate(1.0)
    time.sleep(sleep_time)
    return n * n


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        controller = JobController(executor=executor)

        def got_result(obj, name, arg):
            print "Got result: ", obj, name, arg

        def got_exception(obj, name, arg):
            print "Got exception: ", obj, name, arg

        def got_state_change(obj, name, old, new):
            print "State for {} changed from {} to {}".format(obj, old, new)

        jobs = [
            Job(job=slow_square, args=(n,))
            for n in range(10)
        ]

        # Set up listeners.
        for job in jobs:
            job.on_trait_change(got_result, 'result')
            job.on_trait_change(got_exception, 'exception')
            job.on_trait_change(got_state_change, 'state')

        for job in jobs:
            controller.submit(job)

        controller.run_loop()


if __name__ == '__main__':
    main()
