

class CachedLoader(object):
    items = {}

    @classmethod
    def load_compose_definition(cls, loader: callable):
        if not 'compose' in cls.items:
            cls.items['compose'] = loader()

        return cls.items['compose']
