
from rkd_harbor.cached_loader import CachedLoader
from rkd_harbor.test import BaseHarborTestClass


class CachedLoaderTest(BaseHarborTestClass):
    def test_cached_calls_loader_once(self):
        test = 0

        def loader(num: int):
            return num + 1

        # called triple, but number increased once - the result is cached so the callback is not called more times
        test = CachedLoader.cached('test', lambda: loader(test))
        test = CachedLoader.cached('test', lambda: loader(test))
        test = CachedLoader.cached('test', lambda: loader(test))

        self.assertEqual(test, 1)
