"""
hiku.result
~~~~~~~~~~~

In all examples query results are showed in **denormalized** form, suitable
for reading (by humans) and for serializing into simple formats, into `JSON`
for example. But this is not how `Hiku` stores result internally.

Internally `Hiku` stores result in a fully **normalized** form. So result in
`Hiku` is also a graph structure with references between objects. This
approach has lots of advantages:

  - normalization helps to heavily reduce size of serialized result when we
    need to transfer it (this avoids data duplication)
  - it reduces internal memory usage and simplifies work with data
    internally
  - gives ability to cache, precisely and effortlessly update local state
    on the client

"""

import typing as t

from functools import cached_property
from collections import defaultdict

from .scalar import ScalarMeta
from .types import (
    RecordMeta,
    OptionalMeta,
    SequenceMeta,
    get_type,
    GenericMeta,
)
from .query import Base as QueryBase, FieldBase, Fragment, Node, Field, Link
from .graph import (
    Link as GraphLink,
    Field as GraphField,
    MaybeMany,
    Node as GraphNode,
    Many,
    Maybe,
    Graph,
)


class Reference:
    __slots__ = ("node", "ident")

    def __init__(self, node: str, ident: t.Any) -> None:
        self.node = node
        self.ident = ident

    def __repr__(self) -> str:
        return "<{}[{!r}]>".format(self.node, self.ident)

    def __hash__(self) -> int:
        return hash((self.node, self.ident))


ROOT = Reference("__root__", "__root__")


class Index(defaultdict):
    def __init__(self) -> None:
        super(Index, self).__init__(lambda: defaultdict(dict))

    @cached_property
    def root(self) -> t.Dict:
        return self[ROOT.node][ROOT.ident]

    def finish(self) -> None:
        for value in self.values():
            value.default_factory = None
        self.default_factory = None


class Proxy:
    """Proxy is a dict-like interface to index."""

    __slots__ = ("__idx__", "__ref__", "__node__")

    def __init__(self, index: Index, reference: Reference, node: Node) -> None:
        self.__idx__ = index
        self.__ref__ = reference
        self.__node__ = node

    def __repr__(self) -> str:
        return "<Proxy {}>".format(self.__ref__)

    def __getitem__(self, item: str) -> t.Any:
        try:
            field: t.Union[Field, Link] = self.__node__.result_map[item]
        except KeyError:
            raise KeyError(
                "Field {!r} wasn't requested in the query".format(item)
            )

        try:
            obj: t.Dict = self.__idx__[self.__ref__.node][self.__ref__.ident]
        except KeyError:
            raise AssertionError(
                "Object {}[{!r}] is missing in the index".format(
                    self.__ref__.node, self.__ref__.ident
                )
            )

        try:
            value: t.Any = obj[field.index_key]
        except KeyError:
            raise AssertionError(
                "Field {}[{!r}].{} is missing in the index".format(
                    self.__ref__.node, self.__ref__.ident, field.index_key
                )
            )

        if isinstance(field, Field):
            return value
        elif isinstance(value, Reference):
            return self.__class__(self.__idx__, value, field.node)
        elif isinstance(value, list) and value:
            values = []
            for val in value:
                if isinstance(val, Reference):
                    values.append(self.__class__(self.__idx__, val, field.node))
                else:
                    values.append(val)

            return values
        else:
            return value

    def __getattr__(self, name: str) -> t.Any:
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(e)


def _denormalize_type(
    type_: t.Union[GenericMeta, ScalarMeta],
    result: t.Any,
    query_obj: t.Union[FieldBase, Fragment],
) -> t.Any:
    if isinstance(query_obj, Field):
        return result
    elif isinstance(query_obj, Link):
        if isinstance(type_, SequenceMeta):
            return [
                _denormalize_type(type_.__item_type__, item, query_obj)
                for item in result
            ]
        elif isinstance(type_, OptionalMeta):
            return (
                _denormalize_type(type_.__type__, result, query_obj)
                if result is not None
                else None
            )
        else:
            assert isinstance(type_, RecordMeta), type(type_)
            field_types = type_.__field_types__
            return {
                f.name: _denormalize_type(
                    field_types[f.name], result[f.name], f
                )
                for f in query_obj.node.fields
            }
    assert False, (type_, query_obj)


def _denormalize(
    graph: Graph,
    graph_obj: t.Union[GraphNode, GraphField, GraphLink],
    result: t.Any,
    query_obj: QueryBase,
) -> t.Any:
    if isinstance(query_obj, Node):
        assert isinstance(graph_obj, GraphNode)
        r = {}
        for f in query_obj.fields:
            r[f.result_key] = _denormalize(
                graph, graph_obj.fields_map[f.name], result[f.result_key], f
            )
        for fr in query_obj.fragments:
            r.update(
                _denormalize(
                    graph, graph.nodes_map[fr.type_name], result, fr.node
                )
            )

        return r

    elif isinstance(query_obj, Field):
        return result

    elif isinstance(query_obj, Link):
        if isinstance(graph_obj, GraphField):
            assert graph_obj.type is not None
            field_type = get_type(graph.data_types, graph_obj.type)
            assert field_type is not None
            return _denormalize_type(field_type, result, query_obj)

        elif isinstance(graph_obj, GraphLink):
            graph_node = graph.nodes_map[graph_obj.node]
            if graph_obj.type_enum is Many:
                return [
                    _denormalize(graph, graph_node, v, query_obj.node)
                    for v in result
                ]
            elif graph_obj.type_enum is MaybeMany:
                return [
                    (
                        _denormalize(graph, graph_node, v, query_obj.node)
                        if v is not None
                        else None
                    )
                    for v in result
                ]
            elif graph_obj.type_enum is Maybe and result is None:
                return None
            else:
                return _denormalize(graph, graph_node, result, query_obj.node)

        else:
            return _denormalize(graph, graph_obj, result, query_obj.node)


def denormalize(graph: Graph, result: Proxy) -> t.Dict:
    """Transforms normalized result (graph) into simple hierarchical structure

    This hierarchical structure will follow query structure.

    .. note:: To work properly this function requires that incoming query
        was merged by using :py:func:`hiku.query.merge` function. This is done
        by default in all query readers.

    Example:

    .. code-block:: python

        query = hiku.readers.graphql.read('{ foo }')
        norm_result = hiku_engine.execute(graph, query)
        result = hiku.result.denormalize(graph, norm_result)
        assert result == {'foo': 'value'}

    :param graph: :py:class:`~hiku.graph.Graph` definition
    :param result: result of the query
    """
    return _denormalize(graph, graph.root, result, result.__node__)
