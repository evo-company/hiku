from itertools import chain
from collections import OrderedDict

from .types import to_instance
from .utils import kw_only, cached_property


class Option(object):

    def __init__(self, name, *other, **kwargs):
        if not len(other):
            type_ = None
        elif len(other) == 1:
            type_, = other
        else:
            raise TypeError('More positional arguments ({}) than expected (2)'
                            .format(len(other) + 1))

        self.name = name
        self.type = to_instance(type_) if type_ is not None else None
        self.default, = kw_only(kwargs, [], ['default'])

    def accept(self, visitor):
        return visitor.visit_option(self)


class Field(object):

    def __init__(self, name, *other, **kwargs):
        if not len(other):
            raise TypeError('Missing required argument')
        elif len(other) == 1:
            type_, func = None, other[0]
        elif len(other) == 2:
            type_, func = other
        else:
            raise TypeError('More positional arguments ({}) than expected (3)'
                            .format(len(other) + 1))

        options, doc = kw_only(kwargs, [], ['options', 'doc'])

        self.name = name
        self.type = to_instance(type_) if type_ is not None else None
        self.func = func
        self.options = options or ()
        self.doc = doc

    @cached_property
    def options_map(self):
        return OrderedDict((op.name, op) for op in self.options)

    def accept(self, visitor):
        return visitor.visit_field(self)


class Edge(object):

    def __init__(self, name, fields, **kwargs):
        self.name = name
        self.fields = fields
        self.doc, = kw_only(kwargs, [], ['doc'])

    @cached_property
    def fields_map(self):
        return OrderedDict((f.name, f) for f in self.fields)

    def accept(self, visitor):
        return visitor.visit_edge(self)


class Link(object):

    def __init__(self, name, func, **kwargs):
        edge, requires, to_list, options, doc = \
            kw_only(kwargs, ['edge', 'requires', 'to_list'], ['options', 'doc'])

        self.name = name
        self.func = func
        self.edge = edge
        self.requires = requires
        self.to_list = to_list
        self.options = options or ()
        self.doc = doc

    @cached_property
    def options_map(self):
        return OrderedDict((op.name, op) for op in self.options)

    def accept(self, visitor):
        return visitor.visit_link(self)


class Root(Edge):

    def __init__(self, items):
        super(Root, self).__init__(None, items)


class Graph(object):

    def __init__(self, items):
        self.items = items

    @cached_property
    def root(self):
        return Root(list(chain.from_iterable(e.fields for e in self.items
                                             if e.name is None)))

    @cached_property
    def edges(self):
        return [e for e in self.items if e.name is not None]

    @cached_property
    def edges_map(self):
        return OrderedDict((e.name, e) for e in self.edges)

    def accept(self, visitor):
        return visitor.visit_graph(self)


class GraphVisitor(object):

    def visit(self, obj):
        return obj.accept(self)

    def visit_option(self, obj):
        pass

    def visit_field(self, obj):
        for option in obj.options:
            self.visit(option)

    def visit_link(self, obj):
        for option in obj.options:
            self.visit(option)

    def visit_edge(self, obj):
        for item in obj.fields:
            self.visit(item)

    def visit_graph(self, obj):
        for item in obj.items:
            self.visit(item)
