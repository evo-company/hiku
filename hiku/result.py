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
from .types import RecordMeta, OptionalMeta, SequenceMeta
from .query import Node, Field, Link, merge
from .graph import Link as GraphLink, Field as GraphField, Many, Maybe


class Ref(object):

    def __init__(self, index, node, ident):
        self.index = index
        self.node = node
        self.ident = ident

    def __getitem__(self, key):
        return self.index[self.node][self.ident][key]

    def __repr__(self):
        return '<{}:{}>'.format(self.node, self.ident)

    def __eq__(self, other):
        return self.index[self.node][self.ident] == other


class Result(object):
    """Internal result representation

    It gives access to the result of the :py:class:`~hiku.graph.Root` node --
    which is a starting point of the query execution, and from it to all the
    other node objects, which are stored internally in the index.

    Behaves like a mapping.
    """
    def __init__(self):
        self.root = {}
        self.index = {}

    def __getitem__(self, key):
        return self.root[key]

    def ref(self, node, ident):
        return Ref(self.index, node, ident)


def _filter_fields(result, node):
    return {f.name: result[f.name] for f in node.fields}


def _denormalize(graph, graph_obj, result, query_obj):
    if isinstance(query_obj, Node):
        return {f.name: _denormalize(graph, graph_obj.fields_map[f.name],
                                     result[f.name], f)
                for f in query_obj.fields}

    elif isinstance(query_obj, Field):
        return result

    elif isinstance(query_obj, Link):
        if isinstance(graph_obj, GraphField):
            type_ = graph_obj.type
            if isinstance(type_, SequenceMeta):
                return [_filter_fields(item, query_obj.node) for item in result]
            elif isinstance(type_, OptionalMeta):
                return (_filter_fields(result, query_obj.node)
                        if result is not None else None)
            else:
                assert isinstance(type_, RecordMeta), repr(type_)
                return _filter_fields(result, query_obj.node)

        elif isinstance(graph_obj, GraphLink):
            graph_node = graph.nodes_map[graph_obj.node]
            if graph_obj.type_enum is Many:
                return [_denormalize(graph, graph_node, v, query_obj.node)
                        for v in result]
            elif graph_obj.type_enum is Maybe and result is None:
                return None
            else:
                return _denormalize(graph, graph_node, result, query_obj.node)

        else:
            return _denormalize(graph, graph_obj, result, query_obj.node)


def denormalize(graph, result, query):
    """Transforms normalized result (graph) into simple hierarchical structure

    This hierarchical structure will follow query structure.

    Example::

        query = hiku.readers.simple.read('[:foo]')
        norm_result = hiku_engine.execute(graph, query)
        result = hiku.result.denormalize(graph, norm_result, query)
        assert result == {'foo': 'value'}

    :param graph: :py:class:`~hiku.graph.Graph` definition
    :param result: result of the query
    :param query: executed query, instance of the :py:class:`~hiku.query.Node`
    """
    return _denormalize(graph, graph.root, result, merge([query]))
