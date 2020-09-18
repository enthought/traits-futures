# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Example of a custom background job type.
"""

from traits.api import (
    Bool,
    Button,
    HasStrictTraits,
    Instance,
    observe,
    Property,
    Str,
)
from traits_futures.api import TraitsExecutor
from traitsui.api import HGroup, UItem, View

from fizz_buzz_task import FizzBuzzFuture, submit_fizz_buzz


class FizzBuzzUI(HasStrictTraits):
    #: The executor to submit tasks to.
    executor = Instance(TraitsExecutor, ())

    #: The future object returned on task submission.
    future = Instance(FizzBuzzFuture)

    #: Status message showing current state or the last-received result.
    message = Str("Ready")

    #: Button to calculate, plus its enabled state.
    calculate = Button()
    can_calculate = Property(Bool(), depends_on="future")

    #: Button to cancel, plus its enabled state.
    cancel = Button()
    can_cancel = Property(Bool(), depends_on="future.cancellable")

    @observe("calculate")
    def _submit_calculation(self, event):
        self.message = "Running"
        self.future = submit_fizz_buzz(self.executor)

    @observe("cancel")
    def _cancel_running_task(self, event):
        self.message = "Cancelling"
        self.future.cancel()

    @observe("future:fizz")
    def _report_fizz(self, event):
        self.message = "Fizz {}".format(event.new)

    @observe("future:buzz")
    def _report_buzz(self, event):
        self.message = "Buzz {}".format(event.new)

    @observe("future:fizz_buzz")
    def _report_fizz_buzz(self, event):
        self.message = "FIZZ BUZZ! {}".format(event.new)

    @observe("future:done")
    def _reset_future(self, event):
        self.message = "Ready"
        self.future = None

    def _get_can_calculate(self):
        return self.future is None

    def _get_can_cancel(self):
        return self.future is not None and self.future.cancellable

    traits_view = View(
        UItem("message", style="readonly"),
        HGroup(
            UItem("calculate", enabled_when="can_calculate"),
            UItem("cancel", enabled_when="can_cancel"),
        ),
        resizable=True,
    )


if __name__ == "__main__":
    FizzBuzzUI().configure_traits()
