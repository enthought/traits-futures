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
Test support, providing the ability to run the event loop from tests.
"""

from pyface.qt.QtCore import QObject, Qt, QTimer, Signal, Slot
from pyface.qt.QtGui import QApplication

from traits_futures.i_event_loop_helper import IEventLoopHelper


class AttributeSetter(QObject):
    """
    Simple QObject that allows us to set object attributes from with
    a running event loop.
    """

    @Slot(object, str, object)
    def _on_setattr(self, obj, name, value):
        """
        Slot for setting an arbitrary attribute value on an object.
        """
        setattr(obj, name, value)

    #: Signal used to trigger setattr operations.
    setattr = Signal(object, str, object)


@IEventLoopHelper.register
class EventLoopHelper:
    """
    Support for running the Qt event loop in unit tests.
    """

    def init(self):
        """
        Prepare the event loop for use.
        """
        qt_app = QApplication.instance()
        if qt_app is None:
            qt_app = QApplication([])
        self.qt_app = qt_app

        self._attribute_setter = AttributeSetter()
        self._attribute_setter.setattr.connect(
            self._attribute_setter._on_setattr, Qt.QueuedConnection
        )

    def dispose(self):
        """
        Dispose of any resources used by this object.
        """
        self._attribute_setter.setattr.disconnect(
            self._attribute_setter._on_setattr
        )

        del self._attribute_setter
        del self.qt_app

    def setattr_soon(self, obj, name, value):
        """
        Arrange for an attribute to be set once the event loop is running.

        In typical usage, *obj* will be a ``HasTraits`` instance and
        *name* will be the name of a trait on *obj*.

        This method is not thread-safe. It's designed to be called
        from the main thread.

        Parameters
        ----------
        obj : object
            Object to set the given attribute on.
        name : str
            Name of the attribute to set; typically this is
            a traited attribute.
        value : object
            Value to set the attribute to.
        """
        self._attribute_setter.setattr.emit(obj, name, value)

    def run_until(self, object, trait, condition, timeout):
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
        condition
            Single-argument callable, returning a boolean. This will be
            called with *object* as the only input.
        timeout : float
            Number of seconds to allow before timing out with an exception.

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

        def stop_if_condition(event):
            if condition(object):
                qt_app.exit(0)

        object.observe(stop_if_condition, trait)
        try:
            # The condition may have become True before we
            # started listening to changes. So start with a check.
            if condition(object):
                timed_out = 0
            else:
                timeout_timer.timeout.connect(stop_on_timeout)
                timeout_timer.start()
                try:
                    # Qt wrapper support is a bit of a mess here. PyQt6 has
                    # only "exec". PyQt5 and PySide6 support both "exec" and
                    # "exec_", with "exec" the preferred spelling. PyQt4 and
                    # PySide2 support only "exec_".
                    try:
                        exec_method = qt_app.exec
                    except AttributeError:
                        exec_method = qt_app.exec_
                    timed_out = exec_method()
                finally:
                    timeout_timer.stop()
                    timeout_timer.timeout.disconnect(stop_on_timeout)
        finally:
            object.observe(stop_if_condition, trait, remove=True)

        if timed_out:
            raise RuntimeError(
                "run_until timed out after {} seconds. "
                "At timeout, condition was {}.".format(
                    timeout, condition(object)
                )
            )
