# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Example of GUI that runs a time-consuming calculation in the background.

This example demonstrates the difficulties of updating the
main GUI in response to the results of the background task.
"""

import concurrent.futures
import time

from traits.api import Button, HasStrictTraits, Instance, observe, Range, Str
from traitsui.api import Item, UItem, View


def slow_square(input):
    """
    Square a number, slowly.
    """
    # Simulate a slow calculation
    time.sleep(10.0)
    return input * input


class SlowSquareUI(HasStrictTraits):
    """
    GUI wrapper for the slow_square computation.
    """

    #: concurrent.futures executor providing the worker pool.
    worker_pool = Instance(concurrent.futures.Executor)

    #: Value to square.
    input = Range(0, 100, 35)

    #: Status message.
    message = Str("Click the button to square the input")

    #: Button to start calculation.
    square = Button("square")

    @observe("square")
    def _run_calculation(self, event):
        self.message = f"Calculating square of {self.input} ..."
        future = self.worker_pool.submit(slow_square, self.input)
        future.add_done_callback(self._update_message)

    def _update_message(self, future):
        """
        Update the status when the background calculation completes.
        """
        result = future.result()
        self.message = f"The square of {self.input} is {result}"

    view = View(
        Item("input"),
        UItem("message", style="readonly"),
        UItem("square"),
        resizable=True,
    )


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor() as worker_pool:
        SlowSquareUI(worker_pool=worker_pool).configure_traits()
