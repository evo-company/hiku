from .query import Node, Field, Link


class Handle(object):

    def __init__(self, name=None):
        self.__field_name__ = name
        self.__field_options__ = None
        self.__node_items__ = None

    def __getattr__(self, name):
        assert self.__field_name__ is None, self.__field_name__
        return self.__class__(name)

    def __getitem__(self, items):
        assert self.__node_items__ is None, self.__node_items__
        if isinstance(items, Handle):
            items = [items]
        else:
            assert isinstance(items, tuple)
        self.__node_items__ = items
        return self

    def __call__(self, **options):
        assert self.__field_options__ is None, self.__field_options__
        self.__field_options__ = options
        return self


Q = Handle()


def build(items):
    query_items = []
    for handle in items:
        assert handle.__field_name__ is not None
        if handle.__node_items__ is None:
            query_items.append(Field(handle.__field_name__,
                                     handle.__field_options__))
        else:
            query_items.append(Link(handle.__field_name__,
                                    build(handle.__node_items__),
                                    handle.__field_options__))
    return Node(query_items)
