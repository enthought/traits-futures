# (C) Copyright 2018-2021 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

""" Qt implementation of a Pyface Dialog that listens to
a ProgressFuture.
"""

from pyface.api import Dialog
from pyface.qt import QtCore, QtGui
from traits.api import Any, Bool, Instance, Int, on_trait_change
from traits_futures.api import EXECUTING, StepsFuture

# XXX Fix behaviour on dialog close button. Should match pressing the
#  "cancelling" button. (What do users want?)
# Similarly for doing a Ctrl-C


class ProgressFutureDialog(Dialog):
    """Show a cancellable progress dialog listening to a progress manager."""

    #: Text to show for cancellation label.
    cancel_label = "Cancel"

    #: Text to show for the ok label. (Not used here.)
    ok_label = ""

    #: Whether to show a 'Cancel' button or not.
    cancellable = Bool(True)

    #: The maximum number of steps.
    maximum = Int(0)

    #: Whether to show the percentage complete or not.
    show_percent = Bool(True)

    #: The traited ``Future`` representing the state of the background call.
    progress_future = Instance(StepsFuture)

    def cancel(self):
        """Cancel the job.

        Users of the dialog should call this instead of reaching
        down to the progress manager since this method will prevent
        the job from starting if it has not already.
        """
        self.progress_future.cancel()
        self._cancel_button_control.setEnabled(False)

    # Private implementation ##################################################

    _progress_bar = Any()
    _message_control = Any()
    _cancel_button_control = Any()

    def _create_contents(self, parent):
        layout = QtGui.QVBoxLayout()

        if not self.resizeable:
            layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        layout.addWidget(self._create_message(parent, layout))
        layout.addWidget(self._create_gauge(parent, layout))
        if self.cancellable:
            layout.addWidget(self._create_buttons(parent))

        parent.setLayout(layout)

    def _create_buttons(self, parent):
        buttons = QtGui.QDialogButtonBox()

        # 'Cancel' button.
        btn = buttons.addButton(
            self.cancel_label, QtGui.QDialogButtonBox.RejectRole
        )
        btn.setDefault(True)
        # The QueuedConnection here appears to be necessary to avoid a
        # Qt/macOS bug where the dialog widgets are only partially updated
        # after a button click.
        # xref: https://github.com/enthought/traitsui/issues/1308
        # xref: https://bugreports.qt.io/browse/QTBUG-68067
        buttons.rejected.connect(self.cancel, type=QtCore.Qt.QueuedConnection)
        self._cancel_button_control = btn
        return buttons

    def _create_message(self, dialog, layout):
        self._message_control = QtGui.QLabel(
            self.progress_future.message, dialog
        )
        self._message_control.setAlignment(
            QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft
        )
        return self._message_control

    def _create_gauge(self, dialog, layout):
        self._progress_bar = QtGui.QProgressBar(dialog)
        self._progress_bar.setRange(0, self.maximum)
        self._progress_bar.setValue(self.progress_future.step)
        if self.show_percent:
            self._progress_bar.setFormat("%p%")
        else:
            self._progress_bar.setFormat("%v")
        return self._progress_bar

    @on_trait_change("closing")
    def _destroy_traits_on_dialog_closing(self):
        self._message_control = None
        self._progress_bar = None
        self._cancel_button_control = None

    @on_trait_change("maximum")
    def _update_max_on_progress_bar(self, maximum):
        if self._progress_bar is not None:
            self._progress_bar.setRange(0, maximum)

    @on_trait_change("progress_future:[message,state]")
    def _update_message(self, future, name, new):
        if future.state == EXECUTING and future.message != "":
            message = f"{future.state}: {future.message}"
        else:
            message = f"{future.state}"
        self._message_control.setText(message)

    @on_trait_change("progress_future:steps")
    def _update_maximum(self, steps):
        self.maximum = max(steps, 0)

    @on_trait_change("progress_future:step")
    def _update_value(self, step):
        if self._progress_bar is not None:
            self._progress_bar.setValue(step)

    @on_trait_change("progress_future:done")
    def _on_end(self, event):
        self.close()
