# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

import logging
import random
import time

from traits.api import (
    Button,
    Dict,
    HasStrictTraits,
    Instance,
    List,
    observe,
    Property,
    Range,
    Str,
)
from traits_futures.api import (
    CallFuture,
    CANCELLED,
    CANCELLING,
    COMPLETED,
    EXECUTING,
    FAILED,
    submit_call,
    TraitsExecutor,
    WAITING,
)
from traitsui.api import (
    HGroup,
    Item,
    TabularAdapter,
    TabularEditor,
    UItem,
    VGroup,
    View,
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
        return n * n


class JobTabularAdapter(TabularAdapter):
    columns = [
        ("Job State", "state"),
    ]

    #: Row colors for the table.
    colors = Dict(
        {
            CANCELLED: (255, 0, 0),
            CANCELLING: (255, 128, 0),
            EXECUTING: (128, 128, 255),
            FAILED: (255, 192, 255),
            COMPLETED: (128, 255, 128),
            WAITING: (255, 255, 255),
        }
    )

    #: Text to be displayed for the state column.
    state_text = Property(Str())

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


class SquaringHelper(HasStrictTraits):
    #: The Traits executor for the background jobs.
    traits_executor = Instance(TraitsExecutor)

    #: List of the submitted jobs, for display purposes.
    current_futures = List(Instance(CallFuture))

    #: Start a new squaring operation.
    square = Button()

    #: Cancel all currently executing jobs.
    cancel_all = Button()

    #: Clear completed jobs from the list of current jobs.
    clear_finished = Button()

    #: Value that we'll square.
    input = Range(low=0, high=100)

    @observe("square")
    def _do_slow_square(self, event):
        future = submit_call(self.traits_executor, slow_square, self.input)
        self.current_futures.append(future)

    @observe("cancel_all")
    def _cancel_all_futures(self, event):
        for future in self.current_futures:
            future.cancel()

    @observe("clear_finished")
    def _clear_finished_futures(self, event):
        for future in list(self.current_futures):
            if future.done:
                self.current_futures.remove(future)

    def default_traits_view(self):
        return View(
            HGroup(
                VGroup(
                    Item("input"),
                    UItem("square"),
                    UItem("cancel_all"),
                    UItem("clear_finished"),
                ),
                VGroup(
                    UItem(
                        "current_futures",
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


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            "%(asctime)s %(levelname)-8.8s [%(name)s:%(lineno)s] %(message)s"
        ),
    )
    traits_executor = TraitsExecutor()
    try:
        view = SquaringHelper(traits_executor=traits_executor)
        view.configure_traits()
    finally:
        traits_executor.shutdown()
