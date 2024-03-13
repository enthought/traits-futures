# (C) Copyright 2018-2024 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

"""
Test support, providing the ability to run the event loop from within tests.
"""


import asyncio

from traits.api import Bool, HasStrictTraits

from traits_futures.asyncio.event_loop import AsyncioEventLoop

#: Maximum timeout for blocking calls, in seconds. A successful test should
#: never hit this timeout - it's there to prevent a failing test from hanging
#: forever and blocking the rest of the test suite.
SAFETY_TIMEOUT = 5.0


class _HasBool(HasStrictTraits):
    """
    Simple HasTraits class with a single mutable trait.

    Used in tests that need something mutable and observable.
    """

    #: Simple boolean flag.
    flag = Bool(False)


class TestAssistant:
    """
    Convenience mixin class for tests that need the event loop.

    This class is designed to be used as a mixin alongside unittest.TestCase
    for tests that need to run the event loop as part of the test.

    Most of the logic is devolved to a toolkit-specific EventLoopHelper class.
    """

    def event_loop_factory(self):
        """
        Factory for the event loop.

        Returns
        -------
        event_loop: IEventLoop
        """
        asyncio_event_loop = asyncio.new_event_loop()
        self.addCleanup(asyncio_event_loop.close)
        return AsyncioEventLoop(event_loop=asyncio_event_loop)

    def setUp(self):
        self._event_loop = self.event_loop_factory()
        self._event_loop_helper = self._event_loop.helper()
        self._event_loop_helper.init()

    def tearDown(self):
        self._event_loop_helper.dispose()
        del self._event_loop_helper
        del self._event_loop

    def run_until(self, object, trait, condition, timeout=SAFETY_TIMEOUT):
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
        timeout : float, optional
            Number of seconds to allow before timing out with an exception.
            The (somewhat arbitrary) default is 5 seconds.

        Raises
        ------
        RuntimeError
            If timeout is reached, regardless of whether the condition is
            true or not at that point.
        """
        self._event_loop_helper.run_until(object, trait, condition, timeout)

    def exercise_event_loop(self):
        """
        Exercise the event loop.

        Places a new task on the event loop and runs the event loop
        until that task is complete. The goal is to flush out any other
        tasks that might already be in event loop tasks queue.

        Note that there's no guarantee that this will execute other pending
        event loop tasks. So this method is useful for tests of the form
        "check that nothing bad happens as a result of other pending event
        loop tasks", but it's not safe to use it for tests that *require*
        pending event loop tasks to be processed.
        """
        sentinel = _HasBool()
        self._event_loop_helper.setattr_soon(sentinel, "flag", True)
        self.run_until(sentinel, "flag", lambda sentinel: sentinel.flag)
