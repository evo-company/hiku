from __future__ import absolute_import

from contextlib import contextmanager

from ..types import Record, RecordMeta, OptionalMeta, SequenceMeta, MappingMeta
from ..types import GenericMeta, Unknown
from ..expr.checker import GraphTypes

from .types import TypeDef


# TODO: revisit this
_CONTAINER_TYPES = (
    OptionalMeta,
    SequenceMeta,
    MappingMeta,
    RecordMeta,
)


class TypeDoc(object):

    def __init__(self, type_, description):
        self.__type__ = type_
        self.__type_description__ = description

    def __getattr__(self, name):
        return getattr(self.__type, name)


class GraphTypesEx(GraphTypes):

    def visit(self, obj):
        t = super(GraphTypesEx, self).visit(obj)
        if isinstance(t, GenericMeta) and obj.description is not None:
            t = TypeDoc(t, obj.description)
        return t

    def visit_graph(self, obj):
        types_map = super(GraphTypesEx, self).visit_graph(obj)
        return [TypeDef[n, t] for n, t in types_map.items()
                if t is not Unknown]

    def visit_node(self, obj):
        record = super(GraphTypesEx, self).visit_node(obj)
        return Record[[(n, t) for n, t in record.__field_types__.items()
                       if t is not Unknown]]

    def visit_root(self, obj):
        record = super(GraphTypesEx, self).visit_root(obj)
        return Record[[(n, t) for n, t in record.__field_types__.items()
                       if t is not Unknown]]


class _LinePrinter(object):

    def visit(self, type_):
        return type_.accept(self)

    def visit_boolean(self, type_):
        return 'Boolean'

    def visit_string(self, type_):
        return 'String'

    def visit_integer(self, type_):
        return 'Integer'

    def visit_typeref(self, type_):
        return type_.__type_name__

    def visit_unknown(self, type_):
        return 'Unknown'


class _IndentedPrinter(object):
    _indent_size = 2

    def __init__(self):
        self._indent = 0
        self._buffer = []
        self._descriptions = {}

    @contextmanager
    def _add_indent(self):
        self._indent += 1
        yield
        self._indent -= 1

    def _newline(self):
        self._buffer.append('')

    def _print_call(self, line):
        self._buffer.append((' ' * self._indent_size * self._indent) + line)

    def _print_arg(self, type_):
        if isinstance(type_, TypeDoc):
            self._descriptions[len(self._buffer) - 1] = \
                type_.__type_description__
            type_ = type_.__type__
        if isinstance(type_, _CONTAINER_TYPES):
            with self._add_indent():
                self.visit(type_)
        else:
            self._buffer[-1] += ' ' + _LinePrinter().visit(type_)

    def _iter_lines(self):
        for i, line in enumerate(self._buffer):
            if i in self._descriptions:
                yield line + '  ; {}'.format(self._descriptions[i])
            else:
                yield line

    @classmethod
    def dumps(cls, types):
        printer = cls()
        for i, type_ in enumerate(types):
            if i > 0:
                printer._newline()
            printer.visit(type_)
        return '\n'.join(printer._iter_lines()) + '\n'

    def visit(self, type_):
        type_.accept(self)

    def visit_typedef(self, type_):
        self._print_call('type {}'.format(type_.__type_name__))
        self._print_arg(type_.__type__)

    def visit_record(self, type_):
        self._print_call('Record')
        with self._add_indent():
            for name, field_type in type_.__field_types__.items():
                self._print_call(':{}'.format(name))
                self._print_arg(field_type)

    def visit_sequence(self, type_):
        self._print_call('List')
        self._print_arg(type_.__item_type__)

    def visit_mapping(self, type_):
        self._print_call('Dict')
        self._print_arg(type_.__key_type__)
        self._print_arg(type_.__value_type__)

    def visit_optional(self, type_):
        self._print_call('Option')
        self._print_arg(type_.__type__)


def dumps(graph):
    types = GraphTypesEx().visit(graph)
    return _IndentedPrinter.dumps(types)
