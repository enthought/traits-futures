import random
import time

import concurrent.futures

from traits.api import (
    Button, Color, Enum, HasStrictTraits, Instance, Int, List,
    on_trait_change, Range, Unicode,
)
from traitsui.api import HGroup, Item, TabularEditor, UItem, VGroup, View
from traitsui.tabular_adapter import TabularAdapter

from traits_futures.api import Job, JobController, COMPLETED


def slow_square(n):
    sleep_time = random.expovariate(0.2)
    if sleep_time > 10.0:
        time.sleep(10.0)
        raise RuntimeError("Calculation took too long.")
    else:
        time.sleep(sleep_time)
        return n*n


class JobTabularAdapter(TabularAdapter):
    executing_color = Color(0x8080ff)
    succeeded_color = Color(0x80ff80)
    failed_color = Color(0xffc0ff)
    cancelling_color = Color(0xff8000)
    cancelled_color = Color(0xff0000)

    columns = [
        ('Job State', 'text'),
    ]

    def _get_bg_color(self):
        item = self.item
        if item.state == "Succeeded":
            bg_color = self.succeeded_color
        elif item.state == "Executing":
            bg_color = self.executing_color
        elif item.state == "Failed":
            bg_color = self.failed_color
        elif item.state == "Cancelling":
            bg_color = self.cancelling_color
        elif item.state == "Cancelled":
            bg_color = self.cancelled_color

        return bg_color


class JobWrapper(HasStrictTraits):
    job = Instance(Job)

    arg = Int

    state = Enum("Executing", "Failed", "Succeeded", "Cancelling", "Cancelled")

    text = Unicode

    def cancel(self):
        self.job.cancel()
        self.state = "Cancelling"
        self.text = u"Squaring {}: cancelling".format(self.arg)

    def _text_default(self):
        return u"Squaring {}".format(self.arg)

    @on_trait_change('job:result')
    def _got_result(self, result):
        self.state = "Succeeded"
        self.text = u"Squared {}; result = {}".format(self.arg, result)

    @on_trait_change('job:exception')
    def _got_exception(self, exception):
        self.state = "Failed"
        self.text = u"Square of {} failed : {}".format(self.arg, exception)

    @on_trait_change('job:state')
    def _got_state_change(self, state):
        if state == COMPLETED and self.state == "Cancelling":
            self.state = "Cancelled"
            self.text = u"Squaring {}: Cancelled".format(self.arg)


class SquaringHelper(HasStrictTraits):

    executor = Instance(concurrent.futures.Executor)

    job_controller = Instance(JobController)

    current_jobs = List(JobWrapper)

    calculate = Button

    cancel_all = Button

    clear_completed = Button

    input = Range(low=0, high=100)

    def _calculate_fired(self):
        # Need better API.
        job = Job(
            job=slow_square,
            args=(self.input,),
        )
        wrapper = JobWrapper(job=job, arg=self.input)
        self.current_jobs.append(wrapper)
        self.job_controller.submit(job)

    def _cancel_all_fired(self):
        for job in self.current_jobs:
            if job.state == "Executing":
                job.cancel()

    def _clear_completed_fired(self):
        for job in list(self.current_jobs):
            if job.state in ("Cancelled", "Failed", "Succeeded"):
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
                        editor=TabularEditor(
                            adapter=JobTabularAdapter(),
                            auto_update=True,
                        ),
                    ),
                ),
            ),
            resizable=True,
        )


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        view = SquaringHelper(executor=executor)
        view.configure_traits()
