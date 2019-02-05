# (C) Copyright 2018-2019 Enthought, Inc., Austin, TX
# All rights reserved.

import time

from traits.api import Button, HasTraits, Instance, Int, on_trait_change, Str
from traitsui.api import Item, View

from traits_futures.api import CallFuture, TraitsExecutor


# The target function that we plan to execute in the background.
def slow_square(n):
    """ Square the given input, slowly. """
    time.sleep(2.0)
    return n * n


class QuickStartExample(HasTraits):
    #: The executor to submit tasks to.
    executor = Instance(TraitsExecutor, ())

    #: The future object returned on task submission.
    future = Instance(CallFuture)

    #: Input for the calculation.
    input = Int(10)

    #: Result, in string form.
    result = Str("No result yet")

    #: Button to start the calculation.
    calculate = Button()

    @on_trait_change("calculate")
    def _submit_background_call(self):
        # Returns immediately.
        self.future = self.executor.submit_call(slow_square, self.input)

    @on_trait_change("future:done")
    def _report_result(self, future, name, done):
        self.result = "Square is {}".format(future.result)

    traits_view = View(
        Item("input"),
        Item("result", style="readonly"),
        Item("calculate", enabled_when="future is None or future.done"),
    )


QuickStartExample().configure_traits()
