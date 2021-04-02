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
Tests for the background iteration functionality.
"""
import concurrent.futures
import contextlib
import unittest

from traits_futures.api import MultithreadingContext, TraitsExecutor
from traits_futures.testing.gui_test_assistant import (
    GuiTestAssistant,
    SAFETY_TIMEOUT,
)
from traits_futures.tests.background_iteration_tests import (
    BackgroundIterationTests,
)


class TestBackgroundIteration(
    GuiTestAssistant, BackgroundIterationTests, unittest.TestCase
):
    def setUp(self):
        GuiTestAssistant.setUp(self)
        self._context = MultithreadingContext()
        self.executor = TraitsExecutor(context=self._context)

    def tearDown(self):
        self.halt_executor()
        self._context.close()
        GuiTestAssistant.tearDown(self)

    @contextlib.contextmanager
    def block_worker_pool(self):
        """
        Context manager to temporarily block the workers in the worker pool.
        """
        worker_pool = self.executor._worker_pool
        max_workers = worker_pool._max_workers

        event = self._context.event()

        futures = []
        for _ in range(max_workers):
            futures.append(worker_pool.submit(event.wait))
        try:
            yield
        finally:
            event.set()
            concurrent.futures.wait(futures, timeout=SAFETY_TIMEOUT)
