# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

"""
Tests for the background progress functionality.
"""
import concurrent.futures
import contextlib
import threading
import unittest

from traits_futures.api import TraitsExecutor
from traits_futures.tests.background_progress_tests import (
    BackgroundProgressTests,
)
from traits_futures.toolkit_support import toolkit

GuiTestAssistant = toolkit("gui_test_assistant:GuiTestAssistant")


#: Timeout for blocking operations, in seconds.
TIMEOUT = 10.0


class TestBackgroundProgress(
    GuiTestAssistant, BackgroundProgressTests, unittest.TestCase
):
    def setUp(self):
        GuiTestAssistant.setUp(self)
        self.executor = TraitsExecutor()

    def tearDown(self):
        self.halt_executor()
        GuiTestAssistant.tearDown(self)

    #: Factory for a shared event that can be passed to a worker.
    Event = threading.Event

    @contextlib.contextmanager
    def block_worker_pool(self):
        """
        Context manager to temporarily block the workers in the worker pool.
        """
        worker_pool = self.executor._worker_pool
        max_workers = worker_pool._max_workers

        event = self.Event()

        futures = []
        for _ in range(max_workers):
            futures.append(worker_pool.submit(event.wait))
        try:
            yield
        finally:
            event.set()
            concurrent.futures.wait(futures, timeout=TIMEOUT)
