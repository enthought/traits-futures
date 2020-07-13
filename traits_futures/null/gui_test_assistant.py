# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Test support, providing the ability to run the event loop from tests.
"""

import asyncio


#: Default timeout, in seconds
TIMEOUT = 10.0


class GuiTestAssistant:
    def setUp(self):
        self._event_loop = asyncio.get_event_loop()

    def tearDown(self):
        del self._event_loop

    def run_until(self, object, trait, condition, timeout=TIMEOUT):
        """
        Run event loop until the given condition holds true, or until timeout.

        The condition is re-evaluated, with the object as argument, every time
        the trait changes.

        Parameters
        ----------
        object : HasTraits
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

        timed_out = []

        event_loop = self._event_loop

        def stop_on_timeout():
            timed_out.append(True)
            event_loop.stop()

        def stop_if_condition():
            if condition(object):
                event_loop.stop()

        object.on_trait_change(stop_if_condition, trait)
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
            object.on_trait_change(stop_if_condition, trait, remove=True)

        if timed_out:
            raise RuntimeError(
                "run_until timed out after {} seconds. "
                "At timeout, condition was {}.".format(
                    timeout, condition(object)
                )
            )
