# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

import concurrent.futures
import contextlib
import unittest

from traits_futures.api import MultiprocessingContext, TraitsExecutor
from traits_futures.tests.background_call_tests import BackgroundCallTests
from traits_futures.toolkit_support import toolkit

GuiTestAssistant = toolkit("gui_test_assistant:GuiTestAssistant")


#: Timeout for blocking operations, in seconds.
TIMEOUT = 10.0


class TestBackgroundCallProcess(
    GuiTestAssistant, BackgroundCallTests, unittest.TestCase
):
    def setUp(self):
        GuiTestAssistant.setUp(self)
        self._context = MultiprocessingContext()
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
            concurrent.futures.wait(futures, timeout=TIMEOUT)
