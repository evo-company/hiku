from itertools import chain
from collections import defaultdict


this = object()


class Ref(object):

    def __init__(self, backref, name):
        self.backref = backref
        self.name = name


class Field(object):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return ':{}'.format(self.name)


class Link(object):

    def __init__(self, name, edge):
        self.name = name
        self.edge = edge

    def __repr__(self):
        return '{{:{} {!r}}}'.format(self.name, self.edge)


class Edge(object):

    def __init__(self, fields):
        self.fields = {f.name: f for f in fields}

    def __repr__(self):
        return '[{}]'.format(' '.join(map(repr, self.fields.values())))


def _merge(edges):
    to_merge = defaultdict(list)
    for field in chain.from_iterable(e.fields.values() for e in edges):
        if field.__class__ is Link:
            to_merge[field.name].append(field.edge)
        else:
            yield field
    for name, values in to_merge.items():
        yield Link(name, Edge(_merge(values)))


def merge(edges):
    return Edge(_merge(edges))


def qualified_reqs(ref, reqs):
    edge = Edge(reqs)
    while ref is not this:
        edge = Edge([Link(ref.name, edge)])
        ref = ref.backref
    return edge
