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
Example of popping up a modal progress dialog during a simple call.

Use-case: in a running GUI, we want to make a short-running computation
or service call, let's say taking a few seconds. While the computation or
call is in progress, we want to:

(a) provide some visual feedback to the user to let them know that something is
    happening.
(b) free up the GUI thread so that the GUI doesn't appear to be frozen to
    either the user or the operating system, avoiding system reports of the
    form "Python is not responding".

The solution shown in this example is to push the computation to a background
thread using ``submit_call`` and pop up a simple non-cancellable non-closable
progress dialog while the computation is running. Since all we have is a simple
call, no actuall progress is shown, but depending on the OS and Qt stylesheet
in use, Qt will often animate the progress bar.
"""

from pyface.api import Dialog
from pyface.qt import QtCore, QtGui

from traits.api import Button, HasStrictTraits, Instance, observe, Range
from traitsui.api import Item, UItem, View
from traits_futures.api import TraitsExecutor, CallFuture, submit_call


def fibonacci(n):
    """
    Deliberately inefficient recursive implementation of the Fibonacci series.

    Parameters
    ----------
    n : int
        Nonnegative integer - the index into the Fibonacci series.

    Returns
    -------
    fib : int
        The value of the Fibonacci series at n.
    """
    return n if n < 2 else fibonacci(n - 1) + fibonacci(n - 2)


class NonClosableDialog(QtGui.QDialog):
    """
    Modification of QDialog that does nothing on attempts to close.
    """

    # By default, a QDialog closes when its close button is used, or when
    # the "ESC" key is pressed. Both actions are routed through the dialog's
    # 'reject' method, so we can override that method to prevent closing.

    def reject(self):
        """
        Do nothing on close.
        """


class SlowCallDialog(Dialog):
    """
    Simple Pyface dialog showing a progress bar, a title, and nothing else
    """

    #: The future representing the running background task.
    future = Instance(CallFuture)

    def _create_contents(self, parent):
        # Override base class implementation to provide a simple progress bar.
        progress_bar = QtGui.QProgressBar(parent)
        progress_bar.setRange(0, 0)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(progress_bar)
        parent.setLayout(layout)

    def _create_control(self, parent):
        # Override base class implementation in order to customize title hints,
        # and in particular to remove the close button.
        dlg = NonClosableDialog(
            parent,
            QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint,
        )
        dlg.setWindowTitle(self.title)
        return dlg

    @observe("future:done")
    def _close_dialog_on_future_completion(self, event):
        """
        Close the dialog when the background task completes.
        """
        self.close()


class FibonacciCalculator(HasStrictTraits):
    #: The executor to submit tasks to.
    traits_executor = Instance(TraitsExecutor)

    #: Input for the calculation
    input = Range(20, 40, 35)

    #: Button to start the calculation
    calculate = Button("Calculate")

    @observe("calculate")
    def _submit_background_call(self, event):
        SlowCallDialog(
            future=submit_call(self.traits_executor, fibonacci, self.input),
            title=f"Calculating Fib({self.input}). Please wait.",
        ).open()

    traits_view = View(
        Item("input"),
        UItem("calculate"),
    )


if __name__ == "__main__":
    traits_executor = TraitsExecutor()
    try:
        FibonacciCalculator(traits_executor=traits_executor).configure_traits()
    finally:
        traits_executor.shutdown()
