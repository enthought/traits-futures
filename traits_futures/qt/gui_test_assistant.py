# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

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
        Run the event loop until the given condition holds true, or
        until timeout.

        The condition is re-evaluated, with the object as argument, every time
        the trait changes.

        Raises if timeout is reached, regardless of whether the condition
        is true at that point.
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
            QTimer.singleShot(0, stop_if_condition)
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
                "run_until timed out after {} seconds".format(timeout)
            )
