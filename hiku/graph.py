from collections import OrderedDict

from .types import to_instance
from .utils import kw_only


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
        self.options = OrderedDict((o.name, o) for o in (options or ()))
        self.doc = doc

    def accept(self, visitor):
        return visitor.visit_field(self)


class Edge(object):

    def __init__(self, name, fields, **kwargs):
        self.name = name
        self.fields = OrderedDict((f.name, f) for f in fields)
        self.doc, = kw_only(kwargs, [], ['doc'])

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
        self.options = OrderedDict((o.name, o) for o in (options or ()))
        self.doc = doc

    def accept(self, visitor):
        return visitor.visit_link(self)


class Graph(Edge):

    def __init__(self, items):
        super(Graph, self).__init__(None, items)


class GraphVisitor(object):

    def visit(self, obj):
        return obj.accept(self)

    def visit_option(self, obj):
        pass

    def visit_field(self, obj):
        for option in obj.options.values():
            self.visit(option)

    def visit_link(self, obj):
        for option in obj.options.values():
            self.visit(option)

    def visit_edge(self, obj):
        for item in obj.fields.values():
            self.visit(item)
