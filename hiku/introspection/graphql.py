from __future__ import absolute_import

import re

from itertools import chain
from functools import partial
from collections import namedtuple, OrderedDict

from graphql import print_ast, ast_from_value

from ..graph import Graph, Root, Node, Link, Option, Field, Nothing
from ..graph import GraphVisitor, GraphTransformer
from ..types import TypeRef, String, Sequence, Boolean, Optional, TypeVisitor
from ..types import RecordMeta, AbstractTypeVisitor
from ..compat import async_wrapper, PY3

SCALAR = namedtuple('SCALAR', 'name')
OBJECT = namedtuple('OBJECT', 'name')
INPUT_OBJECT = namedtuple('INPUT_OBJECT', 'alias, name')
INTERFACE = namedtuple('INTERFACE', 'name')
LIST = namedtuple('LIST', 'of_type')
NON_NULL = namedtuple('NON_NULL', 'of_type')

FieldIdent = namedtuple('FieldIdent', 'node, name')
ArgumentIdent = namedtuple('ArgumentIdent', 'node, field, name')

ROOT_NAME = 'Root'


class TypeIdent(AbstractTypeVisitor):

    def __init__(self, graph):
        self._graph = graph

    def visit_any(self, obj):
        return NON_NULL(SCALAR('Any'))

    def visit_mapping(self, obj):
        return NON_NULL(SCALAR('Any'))

    def visit_record(self, obj):
        return NON_NULL(SCALAR('Any'))

    def visit_callable(self, obj):
        raise TypeError('Not expected here: {!r}'.format(obj))

    def visit_sequence(self, obj):
        return NON_NULL(LIST(self.visit(obj.__item_type__)))

    def visit_optional(self, obj):
        return self.visit(obj.__type__).of_type

    def visit_typeref(self, obj):
        if obj.__type_name__ in self._graph.nodes_map:
            return NON_NULL(OBJECT(obj.__type_name__))
        else:
            return NON_NULL(INTERFACE(obj.__type_name__))

    def visit_string(self, obj):
        return NON_NULL(SCALAR('String'))

    def visit_integer(self, obj):
        return NON_NULL(SCALAR('Int'))

    def visit_float(self, obj):
        return NON_NULL(SCALAR('Float'))

    def visit_boolean(self, obj):
        return NON_NULL(SCALAR('Boolean'))


class UnsupportedGraphQLType(TypeError):
    pass


class TypeValidator(TypeVisitor):

    @classmethod
    def is_valid(cls, type_):
        try:
            cls().visit(type_)
        except UnsupportedGraphQLType:
            return False
        else:
            return True

    def visit_any(self, obj):
        raise UnsupportedGraphQLType()

    def visit_record(self, obj):
        # inline Record type can't be directly matched to GraphQL type system
        raise UnsupportedGraphQLType()


def not_implemented(*args, **kwargs):
    raise NotImplementedError(args, kwargs)


def na_maybe(graph):
    return Nothing


def na_many(graph, ids=None, options=None):
    if ids is None:
        return []
    else:
        return [[] for _ in ids]


def _nodes_map(graph):
    return OrderedDict(chain(((n.name, n) for n in graph.nodes),
                             ((ROOT_NAME, graph.root),)))


def schema_link(graph):
    return None


def type_link(graph, options):
    name = options['name']
    if name in _nodes_map(graph):
        return OBJECT(name)
    else:
        return Nothing


def root_schema_types(graph):
    yield SCALAR('String')
    yield SCALAR('Int')
    yield SCALAR('Boolean')
    yield SCALAR('Float')
    yield SCALAR('Any')
    for name in _nodes_map(graph):
        yield OBJECT(name)
    for name, type_ in graph.data_types.items():
        if isinstance(type_, RecordMeta):
            yield INTERFACE(name)
            yield INPUT_OBJECT('I{}'.format(name), name)


def root_schema_query_type(graph):
    return OBJECT(ROOT_NAME)


def type_info(graph, fields, ids):
    for ident in ids:
        if isinstance(ident, OBJECT):
            if ident.name == ROOT_NAME:
                node = graph.root
            else:
                node = graph.nodes_map[ident.name]
            info = {'id': ident,
                    'kind': 'OBJECT',
                    'name': ident.name,
                    'description': node.description}
        elif isinstance(ident, INTERFACE):
            info = {'id': ident,
                    'kind': 'INTERFACE',
                    'name': ident.name,
                    'description': None}
        elif isinstance(ident, INPUT_OBJECT):
            info = {'id': ident,
                    'kind': 'INPUT_OBJECT',
                    'name': ident.alias,
                    'description': None}
        elif isinstance(ident, NON_NULL):
            info = {'id': ident,
                    'kind': 'NON_NULL'}
        elif isinstance(ident, LIST):
            info = {'id': ident,
                    'kind': 'LIST'}
        elif isinstance(ident, SCALAR):
            info = {'id': ident,
                    'name': ident.name,
                    'kind': 'SCALAR'}
        else:
            raise TypeError(repr(ident))
        yield [info.get(f.name) for f in fields]


def type_fields_link(graph, ids, options):
    nodes_map = _nodes_map(graph)
    for ident in ids:
        if isinstance(ident, OBJECT):
            node = nodes_map[ident.name]
            field_idents = [FieldIdent(ident.name, f.name) for f in node.fields]
            if not field_idents:
                raise TypeError('Node "{}" does not contain any typed field, '
                                'which is not acceptable for GraphQL in order '
                                'to define schema type'.format(ident.name))
            yield field_idents
        elif isinstance(ident, (INTERFACE, INPUT_OBJECT)):
            type_ = graph.data_types[ident.name]
            field_idents = [FieldIdent(ident.name, f_name)
                            for f_name, f_type in type_.__field_types__.items()]
            yield field_idents
        else:
            yield []


def type_of_type_link(graph, ids):
    for ident in ids:
        if isinstance(ident, (NON_NULL, LIST)):
            yield ident.of_type
        else:
            yield Nothing


def field_info(graph, fields, ids):
    nodes_map = _nodes_map(graph)
    for ident in ids:
        if ident.node in nodes_map:
            node = nodes_map[ident.node]
            field = node.fields_map[ident.name]
            info = {'id': ident,
                    'name': field.name,
                    'description': field.description,
                    'isDeprecated': False,
                    'deprecationReason': None}
        else:
            info = {'id': ident,
                    'name': ident.name,
                    'description': None,
                    'isDeprecated': False,
                    'deprecationReason': None}
        yield [info[f.name] for f in fields]


def field_type_link(graph, ids):
    nodes_map = _nodes_map(graph)
    type_ident = TypeIdent(graph)
    for ident in ids:
        if ident.node in nodes_map:
            node = nodes_map[ident.node]
            field = node.fields_map[ident.name]
            yield type_ident.visit(field.type)
        else:
            type_ = graph.data_types[ident.node].__field_types__[ident.name]
            yield type_ident.visit(type_)


def field_args_link(graph, ids):
    nodes_map = _nodes_map(graph)
    for ident in ids:
        if ident.node in nodes_map:
            node = nodes_map[ident.node]
            field = node.fields_map[ident.name]
            yield [ArgumentIdent(ident.node, field.name, option.name)
                   for option in field.options]
        else:
            yield []


def input_value_info(graph, fields, ids):
    nodes_map = _nodes_map(graph)
    for ident in ids:
        node = nodes_map[ident.node]
        field = node.fields_map[ident.field]
        option = field.options_map[ident.name]
        if option.default is Nothing:
            default = None
        elif option.default is None:
            # graphql-core currently can't parse/print "null" values
            default = 'null'
        else:
            default = print_ast(ast_from_value(option.default))
        info = {'id': ident,
                'name': option.name,
                'description': option.description,
                'defaultValue': default}
        yield [info[f.name] for f in fields]


def input_value_type_link(graph, ids):
    nodes_map = _nodes_map(graph)
    type_ident = TypeIdent(graph)
    for ident in ids:
        node = nodes_map[ident.node]
        field = node.fields_map[ident.field]
        option = field.options_map[ident.name]
        yield type_ident.visit(option.type)


GRAPH = Graph([
    Node('__Type', [
        Field('id', None, type_info),
        Field('kind', String, type_info),
        Field('name', String, type_info),
        Field('description', String, type_info),

        # OBJECT and INTERFACE only
        Link('fields', Sequence[TypeRef['__Field']], type_fields_link,
             requires='id',
             options=[Option('includeDeprecated', Boolean, default=False)]),

        # OBJECT only
        Link('interfaces', Sequence[TypeRef['__Type']], na_many,
             requires='id'),

        # INTERFACE and UNION only
        Link('possibleTypes', Sequence[TypeRef['__Type']], na_many,
             requires='id'),

        # ENUM only
        Link('enumValues', Sequence[TypeRef['__EnumValue']], na_many,
             requires='id',
             options=[Option('includeDeprecated', Boolean, default=False)]),

        # INPUT_OBJECT only
        Link('inputFields', Sequence[TypeRef['__InputValue']], na_many,
             requires='id'),

        # NON_NULL and LIST only
        Link('ofType', Optional[TypeRef['__Type']], type_of_type_link,
             requires='id'),
    ]),
    Node('__Field', [
        Field('id', None, field_info),
        Field('name', String, field_info),
        Field('description', String, field_info),

        Link('args', Sequence[TypeRef['__InputValue']], field_args_link,
             requires='id'),
        Link('type', TypeRef['__Type'], field_type_link, requires='id'),
        Field('isDeprecated', Boolean, field_info),
        Field('deprecationReason', String, field_info),
    ]),
    Node('__InputValue', [
        Field('id', None, input_value_info),
        Field('name', String, input_value_info),
        Field('description', String, input_value_info),
        Link('type', TypeRef['__Type'], input_value_type_link, requires='id'),
        Field('defaultValue', String, input_value_info),
    ]),
    Node('__Directive', [
        Field('name', String, not_implemented),
        Field('description', String, not_implemented),
        Field('locations', String, not_implemented),  # FIXME: Sequence[String]
        Link('args', Sequence[TypeRef['__InputValue']], not_implemented,
             requires=None),
    ]),
    Node('__EnumValue', [
        Field('name', String, not_implemented),
        Field('description', String, not_implemented),
        Field('isDeprecated', Boolean, not_implemented),
        Field('deprecationReason', String, not_implemented),
    ]),
    Node('__Schema', [
        Link('types', Sequence[TypeRef['__Type']], root_schema_types,
             requires=None),
        Link('queryType', TypeRef['__Type'], root_schema_query_type,
             requires=None),
        Link('directives', Sequence[TypeRef['__Directive']], na_many,
             requires=None),
        Link('mutationType', Optional[TypeRef['__Type']], na_maybe,
             requires=None),
        Link('subscriptionType', Optional[TypeRef['__Type']], na_maybe,
             requires=None),
    ]),
    Root([
        Link('__schema', TypeRef['__Schema'], schema_link, requires=None),
        Link('__type', Optional[TypeRef['__Type']], type_link, requires=None,
             options=[Option('name', String)]),
    ]),
])


class ValidateGraph(GraphVisitor):
    _name_re = re.compile('^[_a-zA-Z]\w*$', re.ASCII if PY3 else 0)

    def __init__(self):
        self._path = []
        self._errors = []

    def _add_error(self, name, description):
        path = '.'.join(self._path + [name])
        self._errors.append('{}: {}'.format(path, description))

    @classmethod
    def validate(cls, graph):
        self = cls()
        self.visit(graph)
        if self._errors:
            raise ValueError('Invalid GraphQL graph:\n{}'
                             .format('\n'.join('- {}'.format(err)
                                               for err in self._errors)))

    def visit_node(self, obj):
        if not self._name_re.match(obj.name):
            self._add_error(obj.name,
                            'Invalid node name: {}'.format(obj.name))
        if obj.fields:
            self._path.append(obj.name)
            super(ValidateGraph, self).visit_node(obj)
            self._path.pop()
        else:
            self._add_error(obj.name,
                            'No fields in the {} node'.format(obj.name))

    def visit_root(self, obj):
        if obj.fields:
            self._path.append('Root')
            super(ValidateGraph, self).visit_root(obj)
            self._path.pop()
        else:
            self._add_error('Root',
                            'No fields in the Root node'.format(obj.name))

    def visit_field(self, obj):
        if not self._name_re.match(obj.name):
            self._add_error(obj.name,
                            'Invalid field name: {}'.format(obj.name))
        super(ValidateGraph, self).visit_field(obj)

    def visit_link(self, obj):
        if not self._name_re.match(obj.name):
            self._add_error(obj.name,
                            'Invalid link name: {}'.format(obj.name))
        super(ValidateGraph, self).visit_link(obj)

    def visit_option(self, obj):
        if not self._name_re.match(obj.name):
            self._add_error(obj.name,
                            'Invalid option name: {}'.format(obj.name))
        super(ValidateGraph, self).visit_option(obj)


class BindToGraph(GraphTransformer):

    def __init__(self, graph):
        self.graph = graph

    def visit_field(self, obj):
        field = super(BindToGraph, self).visit_field(obj)
        field.func = partial(field.func, self.graph)
        return field

    def visit_link(self, obj):
        link = super(BindToGraph, self).visit_link(obj)
        link.func = partial(link.func, self.graph)
        return link


class MakeAsync(GraphTransformer):

    def visit_field(self, obj):
        field = super(MakeAsync, self).visit_field(obj)
        field.func = async_wrapper(field.func)
        return field

    def visit_link(self, obj):
        link = super(MakeAsync, self).visit_link(obj)
        link.func = async_wrapper(link.func)
        return link


def type_name_field_func(node_name, fields, ids=None):
    return [[node_name] for _ in ids] if ids is not None else [node_name]


class AddIntrospection(GraphTransformer):

    def __init__(self, introspection_graph, type_name_field_factory):
        self.introspection_graph = introspection_graph
        self.type_name_field_factory = type_name_field_factory

    def visit_node(self, obj):
        node = super(AddIntrospection, self).visit_node(obj)
        node.fields.append(self.type_name_field_factory(obj.name))
        return node

    def visit_root(self, obj):
        root = super(AddIntrospection, self).visit_root(obj)
        root.fields.append(self.type_name_field_factory(ROOT_NAME))
        return root

    def visit_graph(self, obj):
        graph = super(AddIntrospection, self).visit_graph(obj)
        graph.items.extend(self.introspection_graph.items)
        return graph


class GraphQLIntrospection(GraphTransformer):

    def __type_name__(self, node_name):
        return Field('__typename', String,
                     partial(type_name_field_func, node_name))

    def __introspection_graph__(self, graph):
        return BindToGraph(graph).visit(GRAPH)

    def visit_node(self, obj):
        node = super(GraphQLIntrospection, self).visit_node(obj)
        node.fields.append(self.__type_name__(obj.name))
        return node

    def visit_root(self, obj):
        root = super(GraphQLIntrospection, self).visit_root(obj)
        root.fields.append(self.__type_name__(ROOT_NAME))
        return root

    def visit_graph(self, obj):
        ValidateGraph.validate(obj)
        introspection_graph = self.__introspection_graph__(obj)
        items = [self.visit(node) for node in obj.items]
        items.extend(introspection_graph.items)
        return Graph(items, data_types=obj.data_types)


class AsyncGraphQLIntrospection(GraphQLIntrospection):

    def __type_name__(self, node_name):
        return Field('__typename', String,
                     async_wrapper(partial(type_name_field_func, node_name)))

    def __introspection_graph__(self, graph):
        introspection_graph = BindToGraph(graph).visit(GRAPH)
        introspection_graph = MakeAsync().visit(introspection_graph)
        return introspection_graph
