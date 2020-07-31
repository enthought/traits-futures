# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Using Traits Futures to execute the slow computation
in the background.

Background task is now cancellable _and_ provides
partial results.
"""

import random

from traits.api import (
    Bool,
    Button,
    HasStrictTraits,
    Instance,
    Int,
    observe,
    Property,
    Str,
)
from traitsui.api import HGroup, Item, UItem, View

from traits_futures.api import (
    CANCELLED,
    IFuture,
    submit_iteration,
    TraitsExecutor,
)


def approximate_pi(num_points=10 ** 7):
    # approximate pi/4 by throwing points at a unit square and
    # counting the proportion that land in the quarter circle.
    inside = total = 0
    for i in range(num_points):
        if i > 0 and i % 10 ** 5 == 0:
            yield 4 * inside / total  # <- partial result
        x, y = random.random(), random.random()
        inside += x * x + y * y < 1
        total += 1
    return 4 * inside / total


class CancellableTaskExample(HasStrictTraits):
    #: The executor to submit tasks to.
    executor = Instance(TraitsExecutor, ())

    #: The future object returned on task submission.
    future = Instance(IFuture)

    #: Number of iterations to use.
    iterations = Int(10 ** 7)

    #: Message about state of calculation.
    message = Str("No previous calculation runs")

    #: Button to calculate, plus its enabled state.
    calculate = Button()
    can_calculate = Property(Bool(), depends_on="future")

    #: Button to cancel, plus its enabled state.
    cancel = Button()
    can_cancel = Property(Bool(), depends_on="future.cancellable")

    @observe("calculate")
    def _submit_calculation(self, event):
        self.message = "Calculating π"
        self.future = submit_iteration(
            self.executor, approximate_pi, self.iterations
        )

    @observe("cancel")
    def _request_cancellation(self, event):
        self.future.cancel()
        self.message = "Cancelling"

    @observe("future:done")
    def _report_result(self, event):
        print("self.future.state: ", self.future.state)
        print("self.future.done: ", self.future.done)
        if self.future.state == CANCELLED:
            self.message = "Cancelled"
        else:
            self.message = f"Complete: π ≈ {self.future.result:.6f}"
        self.future = None

    @observe("future:result_event")
    def _report_partial_result(self, event):
        self.message = f"Running: π ≈ {event.new:.6f}"

    def _get_can_calculate(self):
        return self.future is None

    def _get_can_cancel(self):
        return self.future is not None and self.future.cancellable

    traits_view = View(
        Item("iterations"),
        UItem("message", style="readonly"),
        HGroup(
            UItem("calculate", enabled_when="can_calculate"),
            UItem("cancel", enabled_when="can_cancel"),
        ),
        resizable=True,
    )


if __name__ == "__main__":
    CancellableTaskExample().configure_traits()
