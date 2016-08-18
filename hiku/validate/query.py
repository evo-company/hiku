from itertools import repeat

from ..types import AbstractTypeVisitor
from ..query import QueryVisitor
from ..graph import GraphVisitor, Edge, Field, Link
from ..compat import text_type

from .errors import Errors


_undefined = object()


class _AssumeRecord(AbstractTypeVisitor):

    def __init__(self, _nested=False):
        self._nested = _nested

    def visit(self, obj):
        if obj is not None:
            return obj.accept(self)

    def _false(self, obj):
        pass

    visit_boolean, visit_string, visit_integer, visit_mapping, \
        visit_callable = repeat(_false, 5)

    def visit_optional(self, obj):
        if not self._nested:
            return _AssumeRecord(_nested=True).visit(obj.__type__)

    def visit_sequence(self, obj):
        if not self._nested:
            return _AssumeRecord(_nested=True).visit(obj.__item_type__)

    def visit_record(self, obj):
        return list(obj.__field_types__)


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


class _TypeError(TypeError):
    pass


class _OptionTypeValidator(object):

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
        elif obj.type is not None:
            try:
                _OptionTypeValidator(value).visit(obj.type)
            except _TypeError:
                edge, field = self.for_
                type_name = type(value).__name__
                self.errors.report('Invalid type "{}" for option "{}.{}:{}" '
                                   'provided'
                                   .format(type_name, edge, field, obj.name))

    def visit_edge(self, obj):
        assert self.options is None, 'Edge can not have options'


class _RecordFieldsValidator(QueryVisitor):

    def __init__(self, field_names, errors):
        self._field_names = set(field_names)
        self._errors = errors

    def visit_field(self, obj):
        if obj.name not in self._field_names:
            self._errors.report('Unknown field name')
        elif obj.options is not None:
            self._errors.report('Options are not expected')

    def visit_link(self, obj):
        self._errors.report('Not a link')

    def visit_edge(self, obj):
        raise AssertionError('Edge is not expected here')


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
        graph_obj = edge.fields_map.get(obj.name, _undefined)
        if isinstance(graph_obj, Field):
            for_ = (edge.name or 'root', obj.name)
            _ValidateOptions(obj.options, for_, self.errors).visit(graph_obj)

            field_types = _AssumeRecord().visit(graph_obj.type)
            if field_types is not None:
                fields_validator = _RecordFieldsValidator(field_types,
                                                          self.errors)
                for field in obj.edge.fields:
                    fields_validator.visit(field)
            else:
                self.errors.report('Trying to query "{}.{}" simple field '
                                   'as edge'
                                   .format(edge.name or 'root', obj.name))

        elif isinstance(graph_obj, Link):
            linked_edge = self.map[graph_obj.edge]
            for_ = (edge.name or 'root', obj.name)
            _ValidateOptions(obj.options, for_, self.errors).visit(graph_obj)

            self.path.append(linked_edge)
            try:
                self.visit(obj.edge)
            finally:
                self.path.pop()

        elif isinstance(graph_obj, Edge):
            linked_edge = graph_obj
            if obj.options is not None:
                self.errors.report('Options are not possible here')
            self.path.append(linked_edge)
            try:
                self.visit(obj.edge)
            finally:
                self.path.pop()

        elif graph_obj is _undefined:
            self.errors.report('Link "{}" is not implemented in the "{}" edge'
                               .format(obj.name, edge.name or 'root'))
        else:
            raise TypeError(repr(graph_obj))
