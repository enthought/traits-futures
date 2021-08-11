# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

import time

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
from traits_futures.api import CallFuture, submit_call, TraitsExecutor
from traitsui.api import Item, UItem, View


def slow_square(n):
    """Square the given input, slowly."""
    time.sleep(5.0)
    return n * n


class QuickStartExample(HasStrictTraits):
    #: The executor to submit tasks to.
    traits_executor = Instance(TraitsExecutor)

    #: The future object returned on task submission.
    future = Instance(CallFuture)

    #: Input for the calculation.
    input = Int(10)

    #: Copy of the input for the last-run / currently-running calculation.
    input_for_calculation = Int()

    #: Message about state of calculation.
    message = Str("No previous calculation runs")

    #: Button to start the calculation.
    calculate = Button()

    #: Boolean used to decide whether to enable the "calculate" button.
    no_running_future = Property(Bool(), observe="future:done")

    @observe("calculate")
    def _submit_background_call(self, event):
        # Returns immediately.
        input = self.input
        self.input_for_calculation = self.input
        self.message = "Calculating square of {} ...".format(input)
        self.future = submit_call(self.traits_executor, slow_square, input)
        # Keep a record so that we can present messages accurately.
        self.input_for_calculation = input

    @observe("future:done")
    def _report_result(self, event):
        future = event.object
        self.message = "The square of {} is {}.".format(
            self.input_for_calculation, future.result
        )

    def _get_no_running_future(self):
        return self.future is None or self.future.done

    traits_view = View(
        Item("input"),
        UItem("message", style="readonly"),
        UItem("calculate", enabled_when="no_running_future"),
        resizable=True,
    )


if __name__ == "__main__":
    traits_executor = TraitsExecutor()
    try:
        QuickStartExample(traits_executor=traits_executor).configure_traits()
    finally:
        traits_executor.shutdown()
