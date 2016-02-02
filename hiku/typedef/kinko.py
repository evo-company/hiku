from __future__ import absolute_import

from contextlib import contextmanager

from ..types import StringType, ListType
from ..graph import Edge, Link, Field

from .types import TypeDef, TypeRef, Record


def graph_to_types(obj):
    if isinstance(obj, Edge):
        if obj.name:
            return TypeDef(obj.name, Record((f.name, graph_to_types(f))
                                            for f in obj.fields.values()))
        else:
            # root edge
            return [graph_to_types(f) for f in obj.fields.values()]
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


class SchemaPrinter(object):
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

    def _print(self, line):
        self._buffer.append((' ' * self._indent_size * self._indent) + line)

    def _append(self, string):
        self._buffer[-1] += string

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

    def visit_string(self, type_):
        self._append('String')

    def visit_integer(self, type_):
        self._append('Integer')

    def visit_list(self, type_):
        raise NotImplementedError

    def visit_record(self, type_):
        self._print('Record')
        with self._add_indent():
            for name, field_type in type_.fields.items():
                self._print(':{} '.format(name))
                self.visit(field_type)

    def visit_typedef(self, type_):
        self._print('type {}'.format(type_.name))
        with self._add_indent():
            self.visit(type_.type)

    def visit_typeref(self, type_):
        raise NotImplementedError


def dumps(root):
    types = graph_to_types(root)
    return SchemaPrinter.dumps(types)
