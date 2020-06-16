
import unittest
from harbor.cached_loader import CachedLoader


class CachedLoaderTest(unittest.TestCase):
    def test_cached_calls_loader_once(self):
        test = 0

        def loader(num: int):
            return num + 1

        # called triple, but number increased once - the result is cached so the callback is not called more times
        test = CachedLoader.cached('test', lambda: loader(test))
        test = CachedLoader.cached('test', lambda: loader(test))
        test = CachedLoader.cached('test', lambda: loader(test))

        self.assertEqual(test, 1)
