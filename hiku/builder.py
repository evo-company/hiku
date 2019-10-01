from .query import Node, Field, Link


class Handle:

    def __init__(self, name=None, options=None, alias=None, items=None):
        self.__field_name__ = name
        self.__field_options__ = options
        self.__field_alias__ = alias
        self.__node_items__ = items

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

    def __lshift__(self, other):
        assert isinstance(other, Handle), type(other)
        assert not self.__field_options__
        assert not self.__field_alias__
        assert not self.__node_items__
        return self.__class__(other.__field_name__,
                              other.__field_options__,
                              self.__field_name__,  # alias
                              other.__node_items__)

    def __call__(self, **options):
        assert self.__field_options__ is None, self.__field_options__
        self.__field_options__ = options
        return self


Q = Handle()


def build(items):
    """Builds a query

    Example:

    .. code-block:: python

        query = build([
            Q.foo,
            Q.bar(arg=42)[
                Q.baz,
            ],
            Q.aliased << Q.field,
        ])

    :param items: list of fields
    :return: ready to execute query
    """
    query_items = []
    for handle in items:
        assert handle.__field_name__ is not None
        if handle.__node_items__ is None:
            query_items.append(Field(handle.__field_name__,
                                     handle.__field_options__,
                                     handle.__field_alias__))
        else:
            query_items.append(Link(handle.__field_name__,
                                    build(handle.__node_items__),
                                    handle.__field_options__,
                                    handle.__field_alias__))
    return Node(query_items)
