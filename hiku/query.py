from itertools import chain
from collections import defaultdict


def _name_repr(name, options):
    if options is None:
        return ':{}'.format(name)
    else:
        options_repr = ' '.join((':{} {!r}'.format(k, v)
                                 for k, v in options.items()))
        return '(:{} {{{}}})'.format(name, options_repr)


class Field(object):

    def __init__(self, name, options=None):
        self.name = name
        self.options = options

    def __repr__(self):
        return _name_repr(self.name, self.options)

    def accept(self, visitor):
        return visitor.visit_field(self)


class Link(object):

    def __init__(self, name, edge, options=None):
        self.name = name
        self.edge = edge
        self.options = options

    def __repr__(self):
        return '{{{} {!r}}}'.format(_name_repr(self.name, self.options),
                                    self.edge)

    def accept(self, visitor):
        return visitor.visit_link(self)


class Edge(object):

    def __init__(self, fields):
        self.fields = {f.name: f for f in fields}

    def __repr__(self):
        return '[{}]'.format(' '.join(map(repr, self.fields.values())))

    def accept(self, visitor):
        return visitor.visit_edge(self)


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


class QueryVisitor(object):

    def visit(self, obj):
        return obj.accept(self)

    def visit_field(self, obj):
        pass

    def visit_link(self, obj):
        self.visit(obj.edge)

    def visit_edge(self, obj):
        for item in obj.fields.values():
            self.visit(item)
