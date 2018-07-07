from __future__ import division

import random
import time

import concurrent.futures
from six.moves import range

from traits.api import (
    Bool, Button, HasStrictTraits, Instance, Int, List,
    on_trait_change, Property, Range, Str)
from traitsui.api import HGroup, Item, TabularEditor, UItem, VGroup, View
from traitsui.tabular_adapter import TabularAdapter

from traits_futures.api import (
    background_job,
    JobController,
    JobHandle,
    CANCELLED,
    CANCELLING,
    EXECUTING,
    FAILED,
    SUCCEEDED,
    WAITING,
)
from traits_futures.iteration import (
    background_iteration,
    IterationFuture,
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


def pi_approximations(chunk_size=10**7):
    """
    Iterator generating successive approximations to pi,
    computed via Monte Carlo method.
    """
    inside_count = sample_count = 0
    while True:
        for _ in range(chunk_size):
            x = random.uniform(0, 1.0)
            y = random.uniform(0, 1.0)
            sample_count += 1
            inside_count += x * x + y * y <= 1.0
        yield sample_count, 4.0 * inside_count / sample_count


class JobTabularAdapter(TabularAdapter):
    columns = [
        ('Job State', 'state'),
        ('Result', 'result'),
        ('Exception', 'exception'),
    ]

    #: Row colors for the table.
    colors = {
        CANCELLED: 0xff0000,
        CANCELLING: 0xff8000,
        EXECUTING: 0x8080ff,
        FAILED: 0xffc0ff,
        SUCCEEDED: 0x80ff80,
        WAITING: 0xffffff,
    }

    #: Text to be displayed for the exception column
    exception_text = Property

    def _get_bg_color(self):
        return self.colors[self.item.state]

    def _get_exception_text(self):
        job = self.item
        if job.exception is None:
            return "None"
        else:
            return job.exception[0]


class SquaringHelper(HasStrictTraits):
    #: The executor backing the controller.
    executor = Instance(concurrent.futures.Executor)

    #: The controller for the background jobs.
    job_controller = Instance(JobController)

    #: List of the submitted jobs, for display purposes.
    current_jobs = List(JobHandle)

    #: Start a new calculation.
    calculate = Button

    #: Cancel all currently executing jobs.
    cancel_all = Button

    #: Clear completed jobs from the list of current jobs.
    clear_completed = Button

    #: Value that we'll square.
    input = Range(low=0, high=100)

    #: Start pi calculation.
    calculate_pi = Button

    #: Cancel pi calculation
    cancel_pi = Button

    #: Future for pi calculation.
    pi_future = Instance(IterationFuture)

    #: State of pi calculation.
    pi_state = Property(Str, depends_on='pi_future.state')

    #: Current approximation, as a formatted string.
    pi_approximation = Str()

    #: Number of points used in current approximation
    pi_count = Int()

    can_cancel = Property(Bool, depends_on='pi_future.state')

    can_calculate = Property(Bool, depends_on='pi_future.state')

    def _get_can_cancel(self):
        return self.pi_future is not None and self.pi_future.cancellable

    def _get_can_calculate(self):
        return self.pi_future is None or self.pi_future.completed

    def _get_pi_state(self):
        return "None" if self.pi_future is None else self.pi_future.state

    def _calculate_pi_fired(self):
        pi_iteration = background_iteration(pi_approximations)
        self.pi_future = self.job_controller.submit(pi_iteration)

    def _cancel_pi_fired(self):
        self.pi_future.cancel()

    @on_trait_change('pi_future:result')
    def _update_pi_approximation(self, new):
        count, approximation = new
        self.pi_count = count
        self.pi_approximation = format(approximation, ".6f")

    def _calculate_fired(self):
        job = background_job(slow_square, self.input)
        job_handle = self.job_controller.submit(job)
        self.current_jobs.append(job_handle)

    def _cancel_all_fired(self):
        for job in self.current_jobs:
            if job.cancellable:
                job.cancel()

    def _clear_completed_fired(self):
        for job in list(self.current_jobs):
            if job.completed:
                self.current_jobs.remove(job)

    def _job_controller_default(self):
        return JobController(executor=self.executor)

    def default_traits_view(self):
        return View(
            VGroup(
                HGroup(
                    Item('calculate_pi', enabled_when='can_calculate'),
                    Item('cancel_pi', enabled_when='can_cancel'),
                    Item('pi_state', style="readonly"),
                    Item('pi_approximation', style="readonly"),
                    Item('pi_count', style="readonly"),
                ),
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
                            editor=TabularEditor(
                                adapter=JobTabularAdapter(),
                                auto_update=True,
                            ),
                        ),
                    ),
                ),
            ),
            width=1024,
            height=768,
            resizable=True,
        )


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        view = SquaringHelper(executor=executor)
        view.configure_traits()
