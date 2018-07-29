"""
Tests for the TraitsExecutor class.
"""
import concurrent.futures
import unittest

from traits_futures.api import (
    TraitsExecutor,
    RUNNING,
    STOPPING,
    STOPPED,
)


class TestTraitsExecutor(unittest.TestCase):
    def setUp(self):
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=4)

    def tearDown(self):
        self.thread_pool.shutdown()

    def test_initial_state(self):
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=4) as thread_pool:
            executor = TraitsExecutor(thread_pool=thread_pool)

            self.assertEqual(executor.state, RUNNING)
