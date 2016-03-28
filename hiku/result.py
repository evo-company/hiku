from collections import defaultdict

from .query import Edge, Field, Link


class Ref(object):

    def __init__(self, storage, entity, ident):
        self.storage = storage
        self.entity = entity
        self.ident = ident

    def __getitem__(self, key):
        return self.storage[self.entity].get(self.ident)[key]

    def __repr__(self):
        return '<{}:{}>'.format(self.entity, self.ident)

    def __eq__(self, other):
        return self.storage[self.entity].get(self.ident) == other


class State(defaultdict):

    def __init__(self):
        super(State, self).__init__(State)


class Result(State):

    def __init__(self):
        super(Result, self).__init__()
        self.idx = State()

    def ref(self, entity, ident):
        return Ref(self.idx, entity, ident)


def _denormalize(graph, graph_obj, result, query_obj):
    if isinstance(query_obj, Edge):
        return {name: _denormalize(graph, graph_obj.fields[name],
                                   result[name], value)
                for name, value in query_obj.fields.items()}

    elif isinstance(query_obj, Field):
        return result

    elif isinstance(query_obj, Link):
        graph_edge = graph.fields[graph_obj.entity]
        if graph_obj.to_list:
            return [_denormalize(graph, graph_edge, v, query_obj.edge)
                    for v in result]
        else:
            return _denormalize(graph, graph_edge, result, query_obj.edge)


def denormalize(graph, result, query):
    return _denormalize(graph, graph, result, query)
