from itertools import chain
from collections import OrderedDict

from .utils import cached_property


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
        self.fields = fields

    @cached_property
    def fields_map(self):
        return OrderedDict((f.name, f) for f in self.fields)

    def __repr__(self):
        return '[{}]'.format(' '.join(map(repr, self.fields)))

    def accept(self, visitor):
        return visitor.visit_edge(self)


def _merge(edges):
    seen = set()
    to_merge = OrderedDict()
    for field in chain.from_iterable(e.fields for e in edges):
        if field.__class__ is Link:
            to_merge.setdefault(field.name, []).append(field.edge)
        else:
            if field.name not in seen:
                seen.add(field.name)
                yield field
    for name, values in to_merge.items():
        yield Link(name, Edge(list(_merge(values))))


def merge(edges):
    return Edge(list(_merge(edges)))


class QueryVisitor(object):

    def visit(self, obj):
        return obj.accept(self)

    def visit_field(self, obj):
        pass

    def visit_link(self, obj):
        self.visit(obj.edge)

    def visit_edge(self, obj):
        for item in obj.fields:
            self.visit(item)
