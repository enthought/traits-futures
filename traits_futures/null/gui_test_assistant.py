"""
Support for emulating running of the event loop during testing.
"""
from __future__ import absolute_import, print_function, unicode_literals

from traits_futures.null.event_loop import (
    EventLoop,
    clear_event_loop,
    get_event_loop,
    set_event_loop,
)


class GuiTestAssistant(object):
    def setUp(self):
        self.event_loop = EventLoop()
        set_event_loop(self.event_loop)

    def tearDown(self):
        clear_event_loop()
        del self.event_loop

    def run_until(self, object, trait, condition, timeout=10.0):
        """
        Run the event loop until the given condition holds true.

        Rechecks the condition whenever the given trait changes.

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
        timeout : float
            Timeout, in seconds.
        """
        if condition(object):
            return

        event_loop = get_event_loop()

        def stop_on_condition():
            if condition(object):
                event_loop.stop()

        object.on_trait_change(stop_on_condition, trait)
        try:
            event_loop.start(timeout=timeout)
        finally:
            object.on_trait_change(stop_on_condition, trait, remove=True)
