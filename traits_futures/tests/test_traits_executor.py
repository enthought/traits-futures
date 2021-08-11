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
Tests for the TraitsExecutor class.
"""
import contextlib
import unittest

from traits.api import Bool

from traits_futures.api import (
    ETSEventLoop,
    MultithreadingContext,
    TraitsExecutor,
)
from traits_futures.testing.test_assistant import TestAssistant
from traits_futures.tests.traits_executor_tests import (
    ExecutorListener,
    TraitsExecutorTests,
)

#: Maximum timeout for blocking calls, in seconds. A successful test should
#: never hit this timeout - it's there to prevent a failing test from hanging
#: forever and blocking the rest of the test suite.
SAFETY_TIMEOUT = 5.0


class TrackingTraitsExecutor(TraitsExecutor):
    """
    Version of TraitsExecutor that keeps track of whether the default
    methods have been called, for testing purposes.
    """

    #: Have we created a message router?
    _message_router_created = Bool(False)

    def __message_router_default(self):
        self._message_router_created = True
        return TraitsExecutor._TraitsExecutor__message_router_default(self)

    #: Have we created a context?
    _context_created = Bool(False)

    def __context_default(self):
        self._context_created = True
        return TraitsExecutor._TraitsExecutor__context_default(self)


class TestTraitsExecutorCreation(TestAssistant, unittest.TestCase):
    def setUp(self):
        TestAssistant.setUp(self)
        self._context = MultithreadingContext()

    def tearDown(self):
        self._context.close()
        TestAssistant.tearDown(self)

    def test_max_workers(self):
        executor = TraitsExecutor(
            max_workers=11,
            context=self._context,
            event_loop=self._event_loop,
        )
        self.assertEqual(executor._worker_pool._max_workers, 11)
        executor.shutdown(timeout=SAFETY_TIMEOUT)

    def test_max_workers_mutually_exclusive_with_worker_pool(self):
        with self.temporary_worker_pool() as worker_pool:
            with self.assertRaises(TypeError):
                TraitsExecutor(
                    worker_pool=worker_pool,
                    max_workers=11,
                    context=self._context,
                    event_loop=self._event_loop,
                )

    def test_default_context(self):
        with self.temporary_executor(event_loop=self._event_loop) as executor:
            self.assertIsInstance(executor._context, MultithreadingContext)

    def test_default_event_loop(self):
        with self.temporary_executor() as executor:
            self.assertIsInstance(executor._event_loop, ETSEventLoop)

    def test_externally_supplied_context(self):
        context = MultithreadingContext()
        try:
            with self.temporary_executor(
                context=context, event_loop=self._event_loop
            ) as executor:
                self.assertIs(executor._context, context)
            self.assertFalse(context.closed)
        finally:
            context.close()

    def test_owned_context_closed_at_executor_stop(self):
        with self.temporary_executor(event_loop=self._event_loop) as executor:
            context = executor._context
            self.assertFalse(context.closed)
        self.assertTrue(context.closed)

    def test_owned_worker_pool(self):
        executor = TraitsExecutor(
            context=self._context,
            event_loop=self._event_loop,
        )
        worker_pool = executor._worker_pool

        executor.shutdown(timeout=SAFETY_TIMEOUT)

        # Check that the internally-created worker pool has been shut down.
        with self.assertRaises(RuntimeError):
            worker_pool.submit(int)

    def test_thread_pool_argument_deprecated(self):
        with self.temporary_worker_pool() as worker_pool:
            with self.assertWarns(DeprecationWarning) as warning_info:
                executor = TraitsExecutor(
                    thread_pool=worker_pool,
                    context=self._context,
                    event_loop=self._event_loop,
                )
            executor.shutdown(timeout=SAFETY_TIMEOUT)

        # Check we're using the right stack level in the warning.
        _, _, this_module = __name__.rpartition(".")
        self.assertIn(this_module, warning_info.filename)

    def test_shared_worker_pool_stop(self):
        with self.temporary_worker_pool() as worker_pool:
            executor = TraitsExecutor(
                worker_pool=worker_pool,
                context=self._context,
                event_loop=self._event_loop,
            )
            executor.stop()
            self.wait_until_stopped(executor)

            # Check that the the shared worker pool is still usable.
            cf_future = worker_pool.submit(int)
            self.assertEqual(cf_future.result(), 0)

    def test_shared_worker_pool_shutdown(self):
        with self.temporary_worker_pool() as worker_pool:
            executor = TraitsExecutor(
                worker_pool=worker_pool,
                context=self._context,
                event_loop=self._event_loop,
            )
            executor.shutdown(timeout=SAFETY_TIMEOUT)

            # Check that the the shared worker pool is still usable.
            cf_future = worker_pool.submit(int)
            self.assertEqual(cf_future.result(), 0)

    def test_no_objects_created_at_stop(self):
        # An executor that has no jobs submitted to it should not
        # need to instantiate either the context or the message router.
        with self.temporary_worker_pool() as worker_pool:
            executor = TrackingTraitsExecutor(
                worker_pool=worker_pool, event_loop=self._event_loop
            )
            executor.stop()
            self.wait_until_stopped(executor)

        self.assertFalse(
            executor._message_router_created,
            msg="Message router unexpectedly created",
        )
        self.assertFalse(
            executor._context_created,
            msg="Context unexpectedly created",
        )

    def test_no_objects_created_at_shutdown(self):
        # An executor that has no jobs submitted to it should not
        # need to instantiate either the context or the message router.
        with self.temporary_worker_pool() as worker_pool:
            executor = TrackingTraitsExecutor(
                worker_pool=worker_pool, event_loop=self._event_loop
            )
            executor.shutdown(timeout=SAFETY_TIMEOUT)

        self.assertFalse(
            executor._message_router_created,
            msg="Message router unexpectedly created",
        )
        self.assertFalse(
            executor._context_created,
            msg="Context unexpectedly created",
        )

    def wait_until_stopped(self, executor):
        """
        Wait for the executor to reach STOPPED state.
        """
        self.run_until(executor, "stopped", lambda executor: executor.stopped)

    @contextlib.contextmanager
    def temporary_worker_pool(self):
        """
        Create a worker pool that's shut down at the end of the with block.
        """
        worker_pool = self._context.worker_pool(max_workers=4)
        try:
            yield worker_pool
        finally:
            worker_pool.shutdown()

    @contextlib.contextmanager
    def temporary_executor(self, **kwds):
        """
        Create a temporary TraitsExecutor, and shut it down properly after use.
        """
        executor = TraitsExecutor(**kwds)
        try:
            yield executor
        finally:
            executor.shutdown(timeout=SAFETY_TIMEOUT)


class TestTraitsExecutor(
    TestAssistant, TraitsExecutorTests, unittest.TestCase
):
    def setUp(self):
        TestAssistant.setUp(self)
        self._context = MultithreadingContext()
        self.executor = TraitsExecutor(
            context=self._context,
            event_loop=self._event_loop,
        )
        self.listener = ExecutorListener(executor=self.executor)

    def tearDown(self):
        del self.listener
        self.executor.shutdown(timeout=SAFETY_TIMEOUT)
        del self.executor
        self._context.close()
        del self._context
        TestAssistant.tearDown(self)


class TestTraitsExecutorWithExternalWorkerPool(
    TestAssistant, TraitsExecutorTests, unittest.TestCase
):
    def setUp(self):
        TestAssistant.setUp(self)
        self._context = MultithreadingContext()
        self._worker_pool = self._context.worker_pool()
        self.executor = TraitsExecutor(
            context=self._context,
            event_loop=self._event_loop,
            worker_pool=self._worker_pool,
        )
        self.listener = ExecutorListener(executor=self.executor)

    def tearDown(self):
        del self.listener
        self.executor.shutdown(timeout=SAFETY_TIMEOUT)
        del self.executor
        self._worker_pool.shutdown()
        del self._worker_pool
        self._context.close()
        del self._context
        TestAssistant.tearDown(self)
