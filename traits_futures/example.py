import random
import time

import concurrent.futures

from traits.api import Button, HasStrictTraits, Instance, List, Range
from traitsui.api import HGroup, Item, TabularEditor, UItem, VGroup, View
from traitsui.tabular_adapter import TabularAdapter

from traits_futures.api import (
    Job,
    JobController,
    IDLE,
    EXECUTING,
    CANCELLING,
    SUCCEEDED,
    FAILED,
    CANCELLED,
)


def slow_square(n, timeout=10.0):
    """
    Compute the square of an integer, slowly.

    The input should be in the range 0-100. The larger
    the input, the longer the expected time to complete the operation.
    """
    mean_time = (n + 5.0) / 5.0
    sleep_time = random.expovariate(1.0 / mean_time)
    if sleep_time > timeout:
        time.sleep(timeout)
        raise RuntimeError("Calculation took too long.")
    else:
        time.sleep(sleep_time)
        return n*n


class JobTabularAdapter(TabularAdapter):
    columns = [
        ('Argument', 'args'),
        ('Job State', 'state'),
        ('Result', 'result'),
        ('Exception', 'exception'),
    ]

    #: Row colors for the table.
    colors = {
        IDLE: 0xffffff,
        EXECUTING: 0x8080ff,
        CANCELLING: 0xff8000,
        CANCELLED: 0xff0000,
        FAILED: 0xffc0ff,
        SUCCEEDED: 0x80ff80,
    }

    def _get_bg_color(self):
        return self.colors[self.item.state]


class SquaringHelper(HasStrictTraits):
    #: The executor backing the controller.
    executor = Instance(concurrent.futures.Executor)

    #: The controller for the background jobs.
    job_controller = Instance(JobController)

    #: List of the submitted jobs, for display purposes.
    current_jobs = List(Job)

    #: Start a new calculation.
    calculate = Button

    #: Cancel all currently executing jobs.
    cancel_all = Button

    #: Clear completed jobs from the list of current jobs.
    clear_completed = Button

    #: Value that we'll square.
    input = Range(low=0, high=100)

    def _calculate_fired(self):
        job = Job(callable=slow_square, args=(self.input,))
        self.current_jobs.append(job)
        self.job_controller.submit(job)

    def _cancel_all_fired(self):
        for job in self.current_jobs:
            if job.state == "Executing":
                job.cancel()

    def _clear_completed_fired(self):
        for job in list(self.current_jobs):
            if job.completed:
                self.current_jobs.remove(job)

    def _job_controller_default(self):
        return JobController(executor=self.executor)

    def default_traits_view(self):
        return View(
            HGroup(
                VGroup(
                    Item('input'),
                    UItem('calculate'),
                    UItem('cancel_all'),
                    UItem('clear_completed'),
                ),
                VGroup(
                    UItem(
                        'current_jobs',
                        editor=TabularEditor(adapter=JobTabularAdapter(),
                                             auto_update=True),
                    ),
                ),
            ),
            resizable=True,
        )


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        view = SquaringHelper(executor=executor)
        view.configure_traits()
