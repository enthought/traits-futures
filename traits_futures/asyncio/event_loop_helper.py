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

from traits_futures.i_event_loop_helper import IEventLoopHelper


@IEventLoopHelper.register
class EventLoopHelper:
    """
    Support for running the asyncio event loop in unit tests.

    Parameters
    ----------
    event_loop : asyncio.AbstractEventLoop
        The asyncio event loop that this object wraps.
    """

    def __init__(self, event_loop):
        self._event_loop = event_loop

    def init(self):
        """
        Prepare the event loop for use.
        """
        pass

    def dispose(self):
        """
        Dispose of any resources used by this object.
        """
        self._event_loop = None

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
        self._event_loop.call_soon(setattr, obj, name, value)

    def run_until(self, object, trait, condition, timeout):
        """
        Run event loop until a given condition occurs, or timeout.

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
        timed_out = []

        event_loop = self._event_loop

        def stop_on_timeout():
            timed_out.append(True)
            event_loop.stop()

        def stop_if_condition(event):
            if condition(object):
                event_loop.stop()

        object.observe(stop_if_condition, trait)
        try:
            # The condition may have become True before we
            # started listening to changes. So start with a check.
            if not condition(object):
                timer_handle = event_loop.call_later(timeout, stop_on_timeout)
                try:
                    event_loop.run_forever()
                finally:
                    timer_handle.cancel()
        finally:
            object.observe(stop_if_condition, trait, remove=True)

        if timed_out:
            raise RuntimeError(
                "run_until timed out after {} seconds. "
                "At timeout, condition was {}.".format(
                    timeout, condition(object)
                )
            )
