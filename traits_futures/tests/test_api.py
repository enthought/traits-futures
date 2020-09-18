# (C) Copyright 2018-2020 Enthought, Inc., Austin, TX
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in LICENSE.txt and may be redistributed only under
# the conditions described in the aforementioned license. The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
#
# Thanks for using Enthought open source!

import unittest


class TestApi(unittest.TestCase):
    def test_imports(self):
        from traits_futures.api import (  # noqa: F401
            BaseFuture,
            CallFuture,
            CANCELLED,
            CANCELLING,
            COMPLETED,
            EXECUTING,
            ExecutorState,
            FAILED,
            FutureState,
            IFuture,
            IParallelContext,
            ITaskSpecification,
            IterationFuture,
            MultithreadingContext,
            ProgressFuture,
            RUNNING,
            STOPPED,
            STOPPING,
            submit_call,
            submit_iteration,
            submit_progress,
            TraitsExecutor,
            WAITING,
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
