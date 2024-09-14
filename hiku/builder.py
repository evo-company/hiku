from typing import List

from .query import Node, Field, Link


class Handle:
    def __init__(
        self, name=None, options=None, alias=None, items=None, mutation=False
    ):
        self.__field_name__ = name
        self.__field_options__ = options
        self.__field_alias__ = alias
        self.__node_items__ = items
        self.__mutation__ = mutation

    def __getattr__(self, name):
        assert self.__field_name__ is None, self.__field_name__
        return self.__class__(name, mutation=self.__mutation__)

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
        return self.__class__(
            other.__field_name__,
            other.__field_options__,
            self.__field_name__,  # alias
            other.__node_items__,
            other.__mutation__,
        )

    def __call__(self, **options):
        assert self.__field_options__ is None, self.__field_options__
        self.__field_options__ = options
        return self

    def __repr__(self) -> str:
        return "Handle[{}]({})".format(
            "Q" if not self.__mutation__ else "M", id(self)
        )


# Q for query
Q = Handle()
# M for mutation
M = Handle(mutation=True)


def build(items: List[Handle]) -> Node:
    """Builds a query or mutation

    Example:

    .. code-block:: python
        # Query
        query = build([
            Q.foo,
            Q.bar(arg=42)[
                Q.baz,
            ],
            Q.aliased << Q.field,
        ])

        # Mutation
        query = build([
            M.create(arg=42)[
                Q.date_created,
            ],
        ])

    :param items: list of fields
    :return: ready to execute query/mutation
    """
    assert (
        len({i.__mutation__ for i in items}) == 1
    ), "Only queries or mutations are allowed in the query"

    query_items = []
    is_mutation = False

    for handle in items:
        if handle.__mutation__:
            is_mutation = True

        assert handle.__field_name__ is not None
        if handle.__node_items__ is None:
            query_items.append(
                Field(
                    handle.__field_name__,
                    handle.__field_options__,
                    handle.__field_alias__,
                )
            )
        else:
            query_items.append(
                Link(  # type: ignore
                    handle.__field_name__,
                    build(handle.__node_items__),
                    handle.__field_options__,
                    handle.__field_alias__,
                )
            )
    return Node(query_items, ordered=is_mutation)
