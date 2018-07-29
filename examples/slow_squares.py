from __future__ import absolute_import, print_function, unicode_literals

import random
import time

from traits.api import Button, Instance, List, Property, Range
from traitsui.api import (
    Handler, HGroup, Item, TabularEditor, UItem, VGroup, View)
from traitsui.tabular_adapter import TabularAdapter

from traits_futures.api import (
    TraitsExecutor,
    CallFuture,
    CANCELLED,
    CANCELLING,
    EXECUTING,
    FAILED,
    COMPLETED,
    WAITING,
)


def slow_square(n, timeout=5.0):
    """
    Compute the square of an integer, slowly and unreliably.

    The input should be in the range 0-100. The larger
    the input, the longer the expected time to complete the operation,
    and the higher the likelihood of timeout.
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
        ('Job State', 'state'),
    ]

    #: Row colors for the table.
    colors = {
        CANCELLED: 0xff0000,
        CANCELLING: 0xff8000,
        EXECUTING: 0x8080ff,
        FAILED: 0xffc0ff,
        COMPLETED: 0x80ff80,
        WAITING: 0xffffff,
    }

    #: Text to be displayed for the state column.
    state_text = Property

    def _get_bg_color(self):
        return self.colors[self.item.state]

    def _get_state_text(self):
        job = self.item
        state = job.state
        state_text = state.title()
        if state == COMPLETED:
            state_text += ": result={}".format(job.result)
        elif state == FAILED:
            state_text += ": {}".format(job.exception[1])
        return state_text


class SquaringHelper(Handler):
    #: The Traits executor for the background jobs.
    traits_executor = Instance(TraitsExecutor, ())

    #: List of the submitted jobs, for display purposes.
    current_futures = List(CallFuture)

    #: Start a new squaring operation.
    square = Button()

    #: Cancel all currently executing jobs.
    cancel_all = Button()

    #: Clear completed jobs from the list of current jobs.
    clear_finished = Button()

    #: Value that we'll square.
    input = Range(low=0, high=100)

    def closed(self, info, is_ok):
        # Cancel all jobs at shutdown.
        self.cancel_all = True
        super(SquaringHelper, self).closed(info, is_ok)

    def _square_fired(self):
        future = self.traits_executor.submit_call(slow_square, self.input)
        self.current_futures.append(future)

    def _cancel_all_fired(self):
        for future in self.current_futures:
            if future.cancellable:
                future.cancel()

    def _clear_finished_fired(self):
        for future in list(self.current_futures):
            if future.done:
                self.current_futures.remove(future)

    def default_traits_view(self):
        return View(
            HGroup(
                VGroup(
                    Item('input'),
                    UItem('square'),
                    UItem('cancel_all'),
                    UItem('clear_finished'),
                ),
                VGroup(
                    UItem(
                        'current_futures',
                        editor=TabularEditor(
                            adapter=JobTabularAdapter(),
                            auto_update=True,
                        ),
                    ),
                ),
            ),
            width=1024,
            height=768,
            resizable=True,
        )


if __name__ == '__main__':
    view = SquaringHelper()
    view.configure_traits()
