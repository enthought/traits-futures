"""
Support for emulating running of the event loop during testing.
"""

# XXX Add support for timeout.
# XXX Add connect and disconnect support for Qt backend
# XXX React only on the appropriate message in the router.
# XXX Router teardown?

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

        Parameters
        ----------
        XXX to do

        Rechecks the condition whenever the given trait changes.
        """
        if condition(object):
            return

        event_loop = get_event_loop()

        def stop_on_condition():
            if condition(object):
                event_loop.stop()

        object.on_trait_change(stop_on_condition, trait)
        try:
            event_loop.run()
        finally:
            object.on_trait_change(stop_on_condition, trait, remove=True)

