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
Test support, providing the ability to run the event loop from tests.
"""

import wx.lib.newevent

from traits_futures.i_event_loop_helper import IEventLoopHelper

# Note: we're not using the more obvious spelling
#   _SetattrEvent, _SetattrEventBinder = wx.lib.newevent.NewEvent()
# here because that confuses Sphinx's autodoc mocking.
# Ref: enthought/traits-futures#263.

#: New event type to be used for signalling attribute set operations.
_SetattrEventPair = wx.lib.newevent.NewEvent()
_SetattrEvent = _SetattrEventPair[0]
_SetattrEventBinder = _SetattrEventPair[1]


# XXX We should be using Pyface's own CallbackTimer instead of creating
# our own, but we were running into segfaults.
# xref: enthought/pyface#815, enthought/traits-futures#251
class TimeoutTimer(wx.Timer):
    """
    Single-shot timer that executes a given callback on completion.

    Parameters
    ----------
    timeout : float
        Timeout in seconds.
    callback : callable
        Callable taking no arguments, to be executed when the timer
        times out.
    args : tuple, optional
        Tuple of positional arguments to pass to the callable. If not
        provided, no positional arguments are passed.
    kwargs : dict, optional
        Dictionary of keyword arguments to pass to the callable. If not
        provided, no keyword arguments are passed.
    """

    def __init__(self, timeout, callback, args=(), kwargs=None):
        wx.Timer.__init__(self)
        self.timeout = timeout
        self.callback = callback
        self.args = args
        self.kwargs = {} if kwargs is None else kwargs

    def start(self):
        """
        Start the timer.
        """
        timeout_in_ms = round(self.timeout * 1000)
        self.StartOnce(milliseconds=timeout_in_ms)

    def stop(self):
        """
        Stop the timer if it hasn't already expired. The callback
        will not be executed.
        """
        self.Stop()

    def Notify(self):
        """
        Execute the callback when the timer completes.
        """
        self.callback(*self.args, **self.kwargs)


class AppForTesting(wx.App):
    """
    Subclass of wx.App used for testing.
    """

    def OnInit(self):
        """
        Override base class to ensure we have at least one window.
        """
        # It's necessary to have at least one window to prevent the application
        # exiting immediately.
        self.frame = wx.Frame(None)
        self.SetTopWindow(self.frame)
        self.frame.Show(False)
        return True

    def exit(self, exit_code):
        """
        Exit the application main event loop with a given exit code.

        The event loop can be started and stopped several times for
        a single AppForTesting object.
        """
        self.exit_code = exit_code
        self.ExitMainLoop()

    def close(self):
        """
        Clean up when the object is no longer needed.
        """
        self.frame.Close()
        del self.frame


class AttributeSetter(wx.EvtHandler):
    """
    Event handler that allows us to set object attributes from with
    a running event loop.
    """

    def _on_setattr(self, event):
        setattr(event.obj, event.name, event.value)


@IEventLoopHelper.register
class EventLoopHelper:
    """
    Support for running the wx event loop in unit tests.
    """

    def init(self):
        """
        Prepare the event loop for use.
        """
        # Running tests requires that there's a visible application.
        self.wx_app = AppForTesting()

        attribute_setter = AttributeSetter()
        attribute_setter.Bind(
            _SetattrEventBinder, handler=attribute_setter._on_setattr
        )

        self._attribute_setter = attribute_setter

    def dispose(self):
        """
        Dispose of any resources used by this object.
        """
        attribute_setter = self._attribute_setter
        attribute_setter.Unbind(
            _SetattrEventBinder, handler=attribute_setter._on_setattr
        )

        del self._attribute_setter

        self.wx_app.close()
        del self.wx_app

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
        event = _SetattrEvent(
            obj=obj,
            name=name,
            value=value,
        )
        wx.PostEvent(self._attribute_setter, event)

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
        condition : callable
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

        wx_app = self.wx_app

        timeout_timer = TimeoutTimer(timeout, lambda: wx_app.exit(1))

        def stop_if_condition(event):
            if condition(object):
                wx_app.exit(0)

        object.observe(stop_if_condition, trait)
        try:
            # The condition may have become True before we
            # started listening to changes. So start with a check.
            if condition(object):
                timed_out = 0
            else:
                timeout_timer.start()
                try:
                    wx_app.MainLoop()
                finally:
                    timed_out = wx_app.exit_code
                    timeout_timer.stop()
        finally:
            object.observe(stop_if_condition, trait, remove=True)

        if timed_out:
            raise RuntimeError(
                "run_until timed out after {} seconds. "
                "At timeout, condition was {}.".format(
                    timeout, condition(object)
                )
            )
