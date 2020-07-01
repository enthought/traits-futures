# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.

import unittest


class TestApi(unittest.TestCase):
    def test_imports(self):
        from traits_futures.api import (  # noqa: F401
            CallFuture,
            CANCELLED,
            CANCELLING,
            COMPLETED,
            EXECUTING,
            ExecutorState,
            FutureState,
            IJobSpecification,
            IterationFuture,
            ProgressFuture,
            RUNNING,
            STOPPED,
            STOPPING,
            submit_call,
            submit_iteration,
            submit_progress,
            TraitsExecutor,
        )

    def test___all__(self):
        import traits_futures.api

        items_in_all = set(traits_futures.api.__all__)
        items_in_api = {
            name
            for name in dir(traits_futures.api)
            if not name.startswith("_")
        }
        self.assertEqual(items_in_all, items_in_api)
