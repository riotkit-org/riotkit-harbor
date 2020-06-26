

class CachedLoader(object):
    items = {}
    is_cache_disabled = False

    @classmethod
    def load_compose_definition(cls, loader: callable):
        return cls.cached('compose', loader)

    @classmethod
    def cached(cls, name: str, loader: callable):
        if name not in cls.items or cls.is_cache_disabled:
            cls.items[name] = loader()

        return cls.items[name]
