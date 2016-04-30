from __future__ import absolute_import

from contextlib import contextmanager

from ..types import ContainerType, RecordType, ListType
from ..graph import Edge, Link, Field

from .types import TypeDef, TypeRef


class TypeDoc(object):

    def __init__(self, type_, doc):
        self.type = type_
        self.doc = doc

    def accept(self, visitor):
        return visitor.visit_typedoc(self)


def _wrap_with_typedoc(func):
    def wrapper(obj):
        type_ = func(obj)
        return TypeDoc(type_, obj.doc) if obj.doc is not None else type_
    return wrapper


@_wrap_with_typedoc
def _translate(obj):
    if isinstance(obj, Edge):
        rec_fields = []
        for f in obj.fields.values():
            if isinstance(f, Field) and f.type is None:
                continue
            rec_fields.append((f.name, _translate(f)))
        return RecordType(rec_fields)
    elif isinstance(obj, Link):
        if obj.to_list:
            return ListType(TypeRef(obj.edge))
        else:
            return TypeRef(obj.edge)
    elif isinstance(obj, Field):
        assert obj.type is not None, repr(obj.type)
        return obj.type
    else:
        raise TypeError(type(obj))


def graph_to_types(root):
    types = []
    for item in root.fields.values():
        if isinstance(item, Field) and item.type is None:
            continue
        types.append(TypeDef(item.name, _translate(item)))
    return types


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
        return type_.name

    def visit_unknown(self, type_):
        return 'Unknown'


class _IndentedPrinter(object):
    _indent_size = 2

    def __init__(self):
        self._indent = 0
        self._buffer = []
        self._docs = {}

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
            self._docs[len(self._buffer) - 1] = type_.doc
            type_ = type_.type
        if isinstance(type_, ContainerType):
            with self._add_indent():
                self.visit(type_)
        else:
            self._buffer[-1] += ' ' + _LinePrinter().visit(type_)

    def _iter_lines(self):
        for i, line in enumerate(self._buffer):
            if i in self._docs:
                yield line + '  ; {}'.format(self._docs[i])
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

    def visit_dict(self, type_):
        self._print_call('Dict')
        self._print_arg(type_.key_type)
        self._print_arg(type_.value_type)

    def visit_option(self, type_):
        self._print_call('Option')
        self._print_arg(type_.type)


def dumps(root):
    types = graph_to_types(root)
    return _IndentedPrinter.dumps(types)
