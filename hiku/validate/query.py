from ..query import QueryVisitor
from ..graph import GraphVisitor
from ..compat import text_type

from .errors import Errors


_undefined = object()


class _AssumeField(GraphVisitor):

    def __init__(self, edge, errors):
        self.edge = edge
        self.errors = errors

    def visit_field(self, obj):
        return True

    def visit_link(self, obj):
        self.errors.report('Trying to query "{}.{}" link as it was a field'
                           .format(self.edge.name or 'root', obj.name))
        return False

    def visit_edge(self, obj):
        assert self.edge.name is None,\
            'Nested edge can be only in the root edge'
        self.errors.report('Trying to query "{}" edge as it was a field'
                           .format(obj.name))
        return False


class _LinkedEdge(GraphVisitor):

    def __init__(self, edge, mapping, errors):
        self.edge = edge
        self.map = mapping
        self.errors = errors

    def visit_field(self, obj):
        self.errors.report('Trying to query "{}.{}" field as edge'
                           .format(self.edge.name or 'root', obj.name))
        return None

    def visit_link(self, obj):
        return self.map[obj.edge]

    def visit_edge(self, obj):
        return self.map[obj.name]


class _TypeError(TypeError):
    pass


class _TypeValidator(object):

    def __init__(self, value):
        self.value = value

    def visit(self, type_):
        type_.accept(self)

    def visit_boolean(self, type_):
        if not isinstance(self.value, bool):
            raise _TypeError('Invalid type')

    def visit_string(self, type_):
        if not isinstance(self.value, text_type):
            raise _TypeError('Invalid type')

    def visit_integer(self, type_):
        if not isinstance(self.value, int):
            raise _TypeError('Invalid type')

    def visit_optional(self, type_):
        if self.value is not None:
            self.visit(type_.__type__)


class _ValidateOptions(GraphVisitor):

    def __init__(self, options, for_, errors):
        self.options = options
        self.for_ = for_
        self.errors = errors
        self._options = options or {}

    def visit_link(self, obj):
        super(_ValidateOptions, self).visit_link(obj)
        unknown = set(self._options).difference(obj.options_map)
        if unknown:
            edge, field = self.for_
            self.errors.report('Unknown options for "{}.{}": {}'.
                               format(edge, field, ', '.join(unknown)))

    visit_field = visit_link

    def visit_option(self, obj):
        default = _undefined if obj.default is None else obj.default
        value = self._options.get(obj.name, default)
        if value is _undefined:
            edge, field = self.for_
            self.errors.report('Required option "{}.{}:{}" is not specified'
                               .format(edge, field, obj.name))
        else:
            try:
                _TypeValidator(value).visit(obj.type)
            except _TypeError:
                edge, field = self.for_
                type_name = type(value).__name__
                self.errors.report('Invalid type "{}" for option "{}.{}:{}" '
                                   'provided'
                                   .format(type_name, edge, field, obj.name))

    def visit_edge(self, obj):
        assert self.options is None, 'Edge can not have options'


class QueryValidator(QueryVisitor):

    def __init__(self, graph):
        self.map = graph.edges_map
        self.path = [graph.root]
        self.errors = Errors()

    def visit_field(self, obj):
        edge = self.path[-1]
        field = edge.fields_map.get(obj.name)
        if field is not None:
            is_field = _AssumeField(edge, self.errors).visit(field)
            if is_field:
                for_ = (edge.name or 'root', obj.name)
                _ValidateOptions(obj.options, for_, self.errors).visit(field)
        else:
            self.errors.report('Field "{}" is not implemented in the "{}" edge'
                               .format(obj.name, edge.name or 'root'))

    def visit_link(self, obj):
        edge = self.path[-1]
        link = edge.fields_map.get(obj.name)
        if link is not None:
            linked_edge = _LinkedEdge(edge, self.map, self.errors).visit(link)
            if linked_edge is not None:
                # link here can be graph.Link or graph.Edge
                for_ = (edge.name or 'root', obj.name)
                _ValidateOptions(obj.options, for_, self.errors).visit(link)
                self.path.append(linked_edge)
                try:
                    super(QueryValidator, self).visit_link(obj)
                finally:
                    self.path.pop()
        else:
            self.errors.report('Link "{}" is not implemented in the "{}" edge'
                               .format(obj.name, edge.name or 'root'))
