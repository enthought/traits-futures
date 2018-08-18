"""
Support for emulating an event loop for testing purposes.
"""
from __future__ import absolute_import, print_function, unicode_literals

from traits_futures.null.event_loop import EventLoop
from traits_futures.null.package_globals import get_event_loop, set_event_loop

#: The default timeout to use, in seconds.
DEFAULT_TIMEOUT = 10.0


class GuiTestAssistant(object):
    def setUp(self):
        # Save the old event loop and create a fresh one for testing.
        self._old_event_loop = get_event_loop()
        self.event_loop = EventLoop()
        set_event_loop(self.event_loop)

    def tearDown(self):
        closed = self.event_loop.run_until_no_handlers(timeout=DEFAULT_TIMEOUT)
        if not closed:
            raise RuntimeError("Not all event loop handlers were closed")

        del self.event_loop
        set_event_loop(self._old_event_loop)
        del self._old_event_loop

    def run_until(self, object, trait, condition, timeout=DEFAULT_TIMEOUT):
        """
        Run the event loop until the given condition holds true.

        Rechecks the condition whenever the given trait changes. If the
        expected condition fails to become true within the given
        timeout, raises a ``RuntimeError``.

        Parameters
        ----------
        object : HasTraits
            Object whose trait we want to listen to.
        trait : str
            Name of the trait to listen to.
        condition : callable
            Callable of a single argument. This is called whenever the
            given trait changes, with the object as its sole argument.
            It should return a bool-like indicating whether to stop
            the event loop.
        timeout : float, optional
            Timeout, in seconds. If not given ``DEFAULT_TIMEOUT`` is used.

        Raises
        ------
        RuntimeError
            If the condition didn't become true before timeout.
        """
        if condition(object):
            return

        event_loop = get_event_loop()

        def stop_on_condition():
            if condition(object):
                event_loop.stop()

        object.on_trait_change(stop_on_condition, trait)
        try:
            stopped = event_loop.start(timeout=timeout)
        finally:
            object.on_trait_change(stop_on_condition, trait, remove=True)

        if not stopped:
            raise RuntimeError(
                "Timeout occurred before the condition became true.")
