# (C) Copyright 2018-2022 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Example of GUI that runs a time-consuming calculation in the main thread.

This example demonstrates that the GUI is unresponsive while the calculation
is running.
"""

import time

from traits.api import Button, HasStrictTraits, observe, Range, Str
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

    #: Value to square.
    input = Range(0, 100, 35)

    #: Status message.
    message = Str("Click the button to square the input")

    #: Button to start calculation.
    square = Button("square")

    @observe("square")
    def _run_calculation(self, event):
        self.message = f"Calculating square of {self.input} ..."
        result = slow_square(self.input)
        self.message = f"The square of {self.input} is {result}"

    view = View(
        Item("input"),
        UItem("message", style="readonly"),
        UItem("square"),
        resizable=True,
    )


if __name__ == "__main__":
    SlowSquareUI().configure_traits()
