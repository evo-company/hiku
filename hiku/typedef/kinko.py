from __future__ import absolute_import

from contextlib import contextmanager

from ..types import StringType, ListType
from ..graph import Edge, Link, Field

from .types import TypeDef, TypeRef, Record


def _translate(obj):
    if isinstance(obj, Edge):
        return Record((f.name, _translate(f)) for f in obj.fields.values())
    elif isinstance(obj, Link):
        if obj.to_list:
            return ListType(TypeRef(obj.entity))
        else:
            return TypeRef(obj.entity)
    elif isinstance(obj, Field):
        # FIXME: annotate all fields with types
        return getattr(obj, 'type', None) or StringType()
    else:
        raise TypeError(type(obj))


def graph_to_types(root):
    types = []
    for item in root.fields.values():
        types.append(TypeDef(item.name, _translate(item)))
    return types


class _LinePrinter(object):

    def visit(self, type_):
        return type_.accept(self)

    def visit_string(self, type_):
        return 'String'

    def visit_integer(self, type_):
        return 'Integer'

    def visit_typeref(self, type_):
        return type_.name


class _IndentedPrinter(object):
    _indent_size = 2

    def __init__(self):
        self._indent = 0
        self._buffer = []

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
        if isinstance(type_, (Record, ListType)):
            # has constructor
            with self._add_indent():
                self.visit(type_)
        else:
            self._buffer[-1] += ' ' + _LinePrinter().visit(type_)

    @classmethod
    def dumps(cls, types):
        printer = cls()
        for i, type_ in enumerate(types):
            if i > 0:
                printer._newline()
            printer.visit(type_)
        return '\n'.join(printer._buffer) + '\n'

    def visit(self, type_):
        type_.accept(self)

    def visit_typedef(self, type_):
        self._print_call('type {}'.format(type_.name))
        self._print_arg(type_.type)

    def visit_record(self, type_):
        self._print_call('Record')
        with self._add_indent():
            for name, field_type in type_.fields.items():
                self._print_call(':{}'.format(name))
                self._print_arg(field_type)

    def visit_list(self, type_):
        self._print_call('List')
        self._print_arg(type_.item_type)


def dumps(root):
    types = graph_to_types(root)
    return _IndentedPrinter.dumps(types)
