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
Test support, providing the ability to run the event loop from tests.
"""

from pyface.qt.QtCore import QTimer
from pyface.qt.QtGui import QApplication


#: Default timeout, in seconds
TIMEOUT = 10.0


class GuiTestAssistant:
    def setUp(self):
        qt_app = QApplication.instance()
        if qt_app is None:
            qt_app = QApplication([])
        self.qt_app = qt_app

    def tearDown(self):
        del self.qt_app

    def run_until(self, object, trait, condition, timeout=TIMEOUT):
        """
        Run event loop until the given condition holds true, or until timeout.

        The condition is re-evaluated, with the object as argument, every time
        the trait changes.

        Parameters
        ----------
        object : traits.has_traits.HasTraits
            Object whose trait we monitor.
        trait : str
            Name of the trait to monitor for changes.
        condition : callable
            Single-argument callable, returning a boolean. This will be
            called with *object* as the only input.
        timeout : float, optional
            Number of seconds to allow before timing out with an exception.
            The (somewhat arbitrary) default is 10 seconds.

        Raises
        ------
        RuntimeError
            If timeout is reached, regardless of whether the condition is
            true or not at that point.
        """

        qt_app = self.qt_app

        timeout_in_ms = round(1000.0 * timeout)
        timeout_timer = QTimer()
        timeout_timer.setSingleShot(True)
        timeout_timer.setInterval(timeout_in_ms)

        def stop_on_timeout():
            qt_app.exit(1)

        def stop_if_condition():
            if condition(object):
                qt_app.exit(0)

        object.on_trait_change(stop_if_condition, trait)
        try:
            # The condition may have become True before we
            # started listening to changes. So start with a check.
            if condition(object):
                timed_out = 0
            else:
                timeout_timer.timeout.connect(stop_on_timeout)
                timeout_timer.start()
                try:
                    timed_out = qt_app.exec_()
                finally:
                    timeout_timer.stop()
                    timeout_timer.timeout.disconnect(stop_on_timeout)
        finally:
            object.on_trait_change(stop_if_condition, trait, remove=True)

        if timed_out:
            raise RuntimeError(
                "run_until timed out after {} seconds. "
                "At timeout, condition was {}.".format(
                    timeout, condition(object)
                )
            )
