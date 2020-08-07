# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Use Traits Futures to approximate π in the background.

Compare with the code in interruptible_task.py.

In this version of the code, pressing the "Cancel" button interrupts the
background task. In addition, the background task provides ongoing progress
information to the UI.
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
    COMPLETED,
    FAILED,
    IFuture,
    submit_call,
    TraitsExecutor,
)


def approximate_pi(num_points=10 ** 7):
    # approximate pi/4 by throwing points at a unit square and
    # counting the proportion that land in the quarter circle.
    inside = total = 0
    for i in range(num_points):
        x, y = random.random(), random.random()
        inside += x * x + y * y < 1
        total += 1
    return 4 * inside / total


class CancellableTaskExample(HasStrictTraits):
    #: The executor to submit tasks to.
    executor = Instance(TraitsExecutor, ())

    #: The future object returned on task submission.
    future = Instance(IFuture)

    #: Number of points to use.
    sample_count = Int(10 ** 7)

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
        self.future = submit_call(
            self.executor, approximate_pi, self.sample_count
        )

    @observe("cancel")
    def _request_cancellation(self, event):
        self.future.cancel()
        self.message = "Cancelling"

    @observe("future:done")
    def _report_result(self, event):
        if self.future.state == CANCELLED:
            self.message = "Cancelled"
        elif self.future.state == FAILED:
            self.message = f"Unexpected error: {self.future.exception[1]}"
        elif self.future.state == COMPLETED:
            self.message = f"Complete: π ≈ {self.future.result:.6f}"
        else:
            # Shouldn't ever get here: CANCELLED, FAILED and COMPLETED
            # are the only possible final states of a future.
            raise RuntimeError(f"Unexpected state: {self.future.state}")
        self.future = None

    def _get_can_calculate(self):
        return self.future is None

    def _get_can_cancel(self):
        return self.future is not None and self.future.cancellable

    traits_view = View(
        Item("sample_count"),
        UItem("message", style="readonly"),
        HGroup(
            UItem("calculate", enabled_when="can_calculate"),
            UItem("cancel", enabled_when="can_cancel"),
        ),
        resizable=True,
    )


if __name__ == "__main__":
    CancellableTaskExample().configure_traits()
