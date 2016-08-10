from collections import defaultdict

from .types import RecordMeta, OptionalMeta, SequenceMeta
from .query import Edge, Field, Link, merge
from .graph import Link as GraphLink, Field as GraphField, Many


class Ref(object):

    def __init__(self, index, edge, ident):
        self.index = index
        self.edge = edge
        self.ident = ident

    def __getitem__(self, key):
        return self.index[self.edge][self.ident][key]

    def __repr__(self):
        return '<{}:{}>'.format(self.edge, self.ident)

    def __eq__(self, other):
        return self.index[self.edge][self.ident] == other


class State(defaultdict):

    def __init__(self):
        super(State, self).__init__(State)


class Result(State):

    def __init__(self):
        super(Result, self).__init__()
        self.index = State()

    def ref(self, edge, ident):
        return Ref(self.index, edge, ident)


def _filter_fields(result, edge):
    return {f.name: result[f.name] for f in edge.fields}


def _denormalize(graph, graph_obj, result, query_obj):
    if isinstance(query_obj, Edge):
        return {f.name: _denormalize(graph, graph_obj.fields_map[f.name],
                                     result[f.name], f)
                for f in query_obj.fields}

    elif isinstance(query_obj, Field):
        return result

    elif isinstance(query_obj, Link):
        if isinstance(graph_obj, GraphField):
            type_ = graph_obj.type
            if isinstance(type_, SequenceMeta):
                return [_filter_fields(item, query_obj.edge) for item in result]
            elif isinstance(type_, OptionalMeta):
                return (_filter_fields(result, query_obj.edge)
                        if result is not None else None)
            else:
                assert isinstance(type_, RecordMeta), repr(type_)
                return _filter_fields(result, query_obj.edge)

        elif isinstance(graph_obj, GraphLink):
            graph_edge = graph.edges_map[graph_obj.edge]
            if graph_obj.type is Many:
                return [_denormalize(graph, graph_edge, v, query_obj.edge)
                        for v in result]
            else:
                return _denormalize(graph, graph_edge, result, query_obj.edge)

        else:
            return _denormalize(graph, graph_obj, result, query_obj.edge)


def denormalize(graph, result, query):
    return _denormalize(graph, graph.root, result, merge([query]))
