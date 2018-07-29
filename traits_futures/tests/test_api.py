from __future__ import absolute_import, print_function, unicode_literals

import unittest


class TestApi(unittest.TestCase):
    def test_imports(self):
        from traits_futures.api import (  # noqa: F401
            TraitsExecutor,
            RUNNING,
            STOPPING,
            STOPPED,
            ExecutorState,

            BackgroundCall,
            CallFuture,

            BackgroundIteration,
            IterationFuture,

            CANCELLED,
            CANCELLING,
            EXECUTING,
            FAILED,
            COMPLETED,
            WAITING,
            FutureState,
        )

    def test___all__(self):
        import traits_futures.api

        future_imports = [
            'absolute_import', 'print_function', 'unicode_literals']
        items_in_all = set(traits_futures.api.__all__)
        items_in_api = {
            name for name in dir(traits_futures.api)
            if not name.startswith('_')
            if name not in future_imports
        }
        self.assertEqual(items_in_all, items_in_api)
