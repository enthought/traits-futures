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
Example showing progress reporting from a background computation, with a
modal progress dialog.
"""
from pyface.qt import QtCore, QtGui
from pyface.ui.qt4.dialog import Dialog
from traits.api import (
    Any,
    Bool,
    Button,
    HasStrictTraits,
    Instance,
    Int,
    observe,
    Property,
    Str,
)
from traits_futures.api import (
    CANCELLED,
    COMPLETED,
    ProgressFuture,
    submit_progress,
    TraitsExecutor,
)
from traitsui.api import HGroup, Item, UItem, VGroup, View


class ProgressDialog(Dialog, HasStrictTraits):
    """
    Dialog showing progress of the prime-counting operation.
    """

    #: The future that we're listening to.
    future = Instance(ProgressFuture)

    #: The message to display.
    message = Str()

    #: The maximum number of steps.
    maximum = Int(1)

    #: The current step.
    value = Int(0)

    def cancel(self):
        """
        Cancel the running future when the cancel button is pressed.
        """
        self.future.cancel()
        self._cancel_button.setEnabled(False)
        self.message = "Cancelling\N{HORIZONTAL ELLIPSIS}"

    # Private traits ##########################################################

    _cancel_button = Any()

    _message_control = Any()

    _progress_bar = Any()

    # Private methods #########################################################

    def _create_contents(self, parent):
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._create_message(parent, layout))
        layout.addWidget(self._create_progress_bar(parent, layout))
        layout.addWidget(self._create_cancel_button(parent))
        parent.setLayout(layout)

    def _create_cancel_button(self, parent):
        buttons = QtGui.QDialogButtonBox()
        self._cancel_button = buttons.addButton(
            "Cancel", QtGui.QDialogButtonBox.RejectRole
        )
        self._cancel_button.setDefault(True)
        buttons.rejected.connect(self.cancel)
        return buttons

    def _create_message(self, dialog, layout):
        self._message_control = QtGui.QLabel(self.message, dialog)
        self._message_control.setAlignment(
            QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft
        )
        return self._message_control

    def _create_progress_bar(self, dialog, layout):
        self._progress_bar = QtGui.QProgressBar(dialog)
        return self._progress_bar

    @observe("message")
    def _update_message(self, event):
        message = event.new
        if self._message_control is not None:
            self._message_control.setText(message)

    @observe("maximum")
    def _update_progress_bar_maximum(self, event):
        maximum = event.new
        if self._progress_bar is not None:
            self._progress_bar.setMaximum(maximum)

    @observe("value")
    def _update_progress_bar_value(self, event):
        value = event.new
        if self._progress_bar is not None:
            self._progress_bar.setValue(value)

    @observe("future:progress")
    def _report_progress(self, event):
        progress_info = event.new
        current_step, max_steps, count_so_far = progress_info
        self.maximum = max_steps
        self.value = current_step
        self.message = "{} of {} chunks processed. {} primes found".format(
            current_step, max_steps, count_so_far
        )

    @observe("future:done")
    def _respond_to_completion(self, event):
        self.future = None
        self.close()


def isqrt(n):
    """
    Find the integer square root of a positive integer.
    """
    s = n
    while True:
        d = n // s
        if s <= d:
            return s
        s = (s + d) // 2


def is_prime(n):
    """
    Determine whether a nonnegative integer is prime.
    """
    return n >= 2 and all(n % d for d in range(2, isqrt(n) + 1))


def count_primes_less_than(n, chunk_size, progress=None):
    """
    Count how many primes there are smaller than n.

    Uses a deliberately inefficient algorithm.
    """
    nchunks = -(-n // chunk_size)
    chunks = [
        (i * chunk_size, min((i + 1) * chunk_size, n)) for i in range(nchunks)
    ]

    prime_count = 0
    for chunk_index, (start, end) in enumerate(chunks):
        progress((chunk_index, nchunks, prime_count))
        prime_count += sum(is_prime(n) for n in range(start, end))
    progress((nchunks, nchunks, prime_count))

    return prime_count


class PrimeCounter(HasStrictTraits):
    """
    UI to compute primes less than a given number.
    """

    #: The Traits executor for the background jobs.
    traits_executor = Instance(TraitsExecutor)

    #: Calculation future.
    future = Instance(ProgressFuture)

    #: Number to count primes up to.
    limit = Int(10 ** 6)

    #: Chunk size to use for the calculation.
    chunk_size = Int(10 ** 4)

    #: Button to start the calculation.
    count = Button()

    #: Bool indicating when the count should be enabled.
    count_enabled = Property(Bool, observe="future.done")

    #: Result from the previous run.
    result_message = Str("No previous result")

    #: Limit used for most recent run.
    _last_limit = Int()

    @observe("count")
    def _count_primes(self, event):
        self._last_limit = self.limit
        self.future = submit_progress(
            self.traits_executor,
            count_primes_less_than,
            self.limit,
            chunk_size=self.chunk_size,
        )
        self.result_message = "Counting ..."

        dialog = ProgressDialog(
            title="Counting primes\N{HORIZONTAL ELLIPSIS}",
            future=self.future,
        )
        dialog.open()

    def _get_count_enabled(self):
        return self.future is None or self.future.done

    @observe("future:done")
    def _report_result(self, event):
        future = event.object
        if future.state == COMPLETED:
            self.result_message = "There are {} primes smaller than {}".format(
                future.result,
                self._last_limit,
            )
        elif future.state == CANCELLED:
            self.result_message = "Run cancelled"

    def default_traits_view(self):
        return View(
            VGroup(
                HGroup(
                    Item("limit", label="Count primes up to"),
                    Item("chunk_size"),
                ),
                HGroup(
                    UItem("count", enabled_when="count_enabled"),
                    UItem("result_message", style="readonly"),
                ),
            ),
            resizable=True,
        )


if __name__ == "__main__":
    traits_executor = TraitsExecutor()
    try:
        view = PrimeCounter(traits_executor=traits_executor)
        view.configure_traits()
    finally:
        traits_executor.shutdown()
