import unittest


class TestApi(unittest.TestCase):
    def test_imports(self):
        from traits_futures.api import (  # noqa
            JobController,
            JobHandle,
            WAITING,
            EXECUTING,
            CANCELLING,
            SUCCEEDED,
            FAILED,
            CANCELLED,
        )

    def test___all__(self):
        import traits_futures.api

        items_in_all = set(traits_futures.api.__all__)
        items_in_api = {
            name for name in dir(traits_futures.api)
            if not name.startswith('_')
        }
        self.assertEqual(items_in_all, items_in_api)
