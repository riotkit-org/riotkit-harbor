

class CachedLoader(object):
    items = {}

    @classmethod
    def load_compose_definition(cls, loader: callable):
        return cls.cached('compose', loader)

    @classmethod
    def cached(cls, name: str, loader: callable):
        if name not in cls.items:
            cls.items[name] = loader()

        return cls.items[name]

    @classmethod
    def clear(cls):
        cls.items = {}
