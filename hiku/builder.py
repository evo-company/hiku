from .query import Node, Field, Link


class Handle(object):

    def __init__(self, name=None):
        self.name = name
        self.options = None
        self.items = None

    def __getattr__(self, name):
        assert self.name is None, self.name
        return self.__class__(name)

    def __getitem__(self, items):
        assert self.items is None, self.items
        if isinstance(items, Handle):
            items = [items]
        else:
            assert isinstance(items, tuple)
        self.items = items
        return self

    def __call__(self, **options):
        assert self.options is None, self.options
        self.options = options
        return self


def build(items):
    query_items = []
    for handle in items:
        assert handle.name is not None
        if handle.items is None:
            query_items.append(Field(handle.name, handle.options))
        else:
            query_items.append(Link(handle.name, build(handle.items),
                                    handle.options))
    return Node(query_items)
