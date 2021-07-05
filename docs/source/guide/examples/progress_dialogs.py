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
Demo script for modal progress dialog.
"""

import concurrent.futures
import time

from traits.api import Any, Button, HasStrictTraits, Instance, List, Range
from traits_futures.api import submit_steps, TraitsExecutor
from traitsui.api import Item, View

from background_progress_dialog import ProgressFutureDialog


def count(target, *, sleep=1.0, progress):
    progress.start("counting", steps=target)
    for i in range(target):
        progress.step(f"step {i} of {target}", step=i)
        time.sleep(sleep)


class MyView(HasStrictTraits):

    calculate = Button()

    nonmodal = Button()

    target = Range(0, 100, 10)

    executor = Instance(TraitsExecutor)

    def _executor_default(self):
        return TraitsExecutor()  # worker_pool=self.cf_executor)

    dialogs = List(ProgressFutureDialog)

    cf_executor = Any()

    def _calculate_fired(self):
        target = self.target
        future = submit_steps(self.executor, count, target=target)
        dialog = ProgressFutureDialog(
            progress_future=future,
            style="modal",  # this is the default
            title=f"Counting to {target}",
        )
        dialog.open()

    def _nonmodal_fired(self):
        target = self.target
        future = submit_steps(self.executor, count, target)
        dialog = ProgressFutureDialog(
            progress_future=future,
            style="nonmodal",  # this is the default
            title=f"Counting to {target}",
        )
        dialog.open()
        # Keep a reference to open dialogs, else they'll
        # mysteriously disappear. A better solution might be to
        # parent them appropriately.
        self.dialogs.append(dialog)

    view = View(
        Item("calculate", label="Count modal"),
        Item("nonmodal", label="Count nonmodal"),
        Item("target"),
    )


def main():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        view = MyView(cf_executor=executor)
        view.configure_traits()


if __name__ == "__main__":
    main()
