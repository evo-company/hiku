import re
import json

from functools import partial
from collections import namedtuple, OrderedDict

from ..graph import Graph, Root, Node, Link, Option, Field, Nothing
from ..graph import GraphVisitor, GraphTransformer
from ..types import TypeRef, String, Sequence, Boolean, Optional, TypeVisitor
from ..types import Any, RecordMeta, AbstractTypeVisitor
from ..utils import listify


def _namedtuple(typename, field_names):
    """Fixes hashing for different tuples with same content
    """
    base = namedtuple(typename, field_names)

    def __hash__(self):
        return hash((self.__class__, super(base, self).__hash__()))

    return type(typename, (base,), {
        '__slots__': (),
        '__hash__': __hash__,
    })


def _async_wrapper(func):
    async def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


SCALAR = _namedtuple('SCALAR', 'name')
OBJECT = _namedtuple('OBJECT', 'name')
DIRECTIVE = _namedtuple('DIRECTIVE', 'name')
INPUT_OBJECT = _namedtuple('INPUT_OBJECT', 'name')
LIST = _namedtuple('LIST', 'of_type')
NON_NULL = _namedtuple('NON_NULL', 'of_type')

FieldIdent = _namedtuple('FieldIdent', 'node, name')
FieldArgIdent = _namedtuple('FieldArgIdent', 'node, field, name')
InputObjectFieldIdent = _namedtuple('InputObjectFieldIdent', 'name, key')
DirectiveArgIdent = _namedtuple('DirectiveArgIdent', 'name')

QUERY_ROOT_NAME = 'Query'
MUTATION_ROOT_NAME = 'Mutation'


class TypeIdent(AbstractTypeVisitor):

    def __init__(self, graph, input_mode=False):
        self._graph = graph
        self._input_mode = input_mode

    def visit_any(self, obj):
        return SCALAR('Any')

    def visit_mapping(self, obj):
        return SCALAR('Any')

    def visit_record(self, obj):
        return SCALAR('Any')

    def visit_callable(self, obj):
        raise TypeError('Not expected here: {!r}'.format(obj))

    def visit_sequence(self, obj):
        return NON_NULL(LIST(self.visit(obj.__item_type__)))

    def visit_optional(self, obj):
        ident = self.visit(obj.__type__)
        return ident.of_type if isinstance(ident, NON_NULL) else ident

    def visit_typeref(self, obj):
        if self._input_mode:
            assert obj.__type_name__ in self._graph.data_types, \
                obj.__type_name__
            return NON_NULL(INPUT_OBJECT(obj.__type_name__))
        else:
            return NON_NULL(OBJECT(obj.__type_name__))

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


def na_maybe(schema):
    return Nothing


def na_many(schema, ids=None, options=None):
    if ids is None:
        return []
    else:
        return [[] for _ in ids]


def _nodes_map(schema):
    nodes = [(n.name, n) for n in schema.query_graph.nodes]
    nodes.append((QUERY_ROOT_NAME, schema.query_graph.root))
    if schema.mutation_graph is not None:
        nodes.append((MUTATION_ROOT_NAME, schema.mutation_graph.root))
    return OrderedDict(nodes)


def schema_link(schema):
    return None


def type_link(schema, options):
    name = options['name']
    if name in _nodes_map(schema):
        return OBJECT(name)
    else:
        return Nothing


@listify
def root_schema_types(schema):
    yield SCALAR('String')
    yield SCALAR('Int')
    yield SCALAR('Boolean')
    yield SCALAR('Float')
    yield SCALAR('Any')
    for name in _nodes_map(schema):
        yield OBJECT(name)
    for name, type_ in schema.data_types.items():
        if isinstance(type_, RecordMeta):
            yield OBJECT(name)
            yield INPUT_OBJECT(name)


def root_schema_query_type(schema):
    return OBJECT(QUERY_ROOT_NAME)


def root_schema_mutation_type(schema):
    if schema.mutation_graph is not None:
        return OBJECT(MUTATION_ROOT_NAME)
    else:
        return Nothing


def root_schema_directives(schema):
    return [DIRECTIVE('skip'), DIRECTIVE('include')]


@listify
def type_info(schema, fields, ids):
    nodes_map = _nodes_map(schema)
    for ident in ids:
        if isinstance(ident, OBJECT):
            if ident.name in nodes_map:
                description = nodes_map[ident.name].description
            else:
                description = None
            info = {'id': ident,
                    'kind': 'OBJECT',
                    'name': ident.name,
                    'description': description}
        elif isinstance(ident, INPUT_OBJECT):
            info = {'id': ident,
                    'kind': 'INPUT_OBJECT',
                    'name': 'IO{}'.format(ident.name),
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


@listify
def type_fields_link(schema, ids, options):
    nodes_map = _nodes_map(schema)
    for ident in ids:
        if isinstance(ident, OBJECT):
            if ident.name in nodes_map:
                node = nodes_map[ident.name]
                field_idents = [
                    FieldIdent(ident.name, f.name)
                    for f in node.fields if not f.name.startswith('_')
                ]
            else:
                type_ = schema.data_types[ident.name]
                field_idents = [
                    FieldIdent(ident.name, f_name)
                    for f_name, f_type in type_.__field_types__.items()
                ]
            if not field_idents:
                raise TypeError('Object type "{}" does not contain fields, '
                                'which is not acceptable for GraphQL in order '
                                'to define schema type'.format(ident.name))
            yield field_idents
        else:
            yield []


@listify
def type_of_type_link(schema, ids):
    for ident in ids:
        if isinstance(ident, (NON_NULL, LIST)):
            yield ident.of_type
        else:
            yield Nothing


@listify
def field_info(schema, fields, ids):
    nodes_map = _nodes_map(schema)
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


@listify
def field_type_link(schema, ids):
    nodes_map = _nodes_map(schema)
    type_ident = TypeIdent(schema.query_graph)
    for ident in ids:
        if ident.node in nodes_map:
            node = nodes_map[ident.node]
            field = node.fields_map[ident.name]
            yield type_ident.visit(field.type or Any)
        else:
            data_type = schema.data_types[ident.node]
            field_type = data_type.__field_types__[ident.name]
            yield type_ident.visit(field_type)


@listify
def field_args_link(schema, ids):
    nodes_map = _nodes_map(schema)
    for ident in ids:
        if ident.node in nodes_map:
            node = nodes_map[ident.node]
            field = node.fields_map[ident.name]
            yield [FieldArgIdent(ident.node, field.name, option.name)
                   for option in field.options]
        else:
            yield []


@listify
def type_input_object_input_fields_link(schema, ids):
    for ident in ids:
        if isinstance(ident, INPUT_OBJECT):
            data_type = schema.data_types[ident.name]
            yield [InputObjectFieldIdent(ident.name, key)
                   for key in data_type.__field_types__.keys()]
        else:
            yield []


_arg_descriptions = {
    'include': (
        'Included when true.'
    ),
    'skip': (
        'Skipped when true.'
    ),
}


@listify
def input_value_info(schema, fields, ids):
    nodes_map = _nodes_map(schema)
    for ident in ids:
        if isinstance(ident, FieldArgIdent):
            node = nodes_map[ident.node]
            field = node.fields_map[ident.field]
            option = field.options_map[ident.name]
            if option.default is Nothing:
                default = None
            else:
                default = json.dumps(option.default)
            info = {'id': ident,
                    'name': option.name,
                    'description': option.description,
                    'defaultValue': default}
            yield [info[f.name] for f in fields]
        elif isinstance(ident, InputObjectFieldIdent):
            info = {'id': ident,
                    'name': ident.key,
                    'description': None,
                    'defaultValue': None}
            yield [info[f.name] for f in fields]
        elif isinstance(ident, DirectiveArgIdent):
            info = {'id': ident,
                    'name': 'if',
                    'description': _arg_descriptions[ident.name],
                    'defaultValue': None}
            yield [info[f.name] for f in fields]
        else:
            raise TypeError(repr(ident))


@listify
def input_value_type_link(schema, ids):
    nodes_map = _nodes_map(schema)
    type_ident = TypeIdent(schema.query_graph, input_mode=True)
    for ident in ids:
        if isinstance(ident, FieldArgIdent):
            node = nodes_map[ident.node]
            field = node.fields_map[ident.field]
            option = field.options_map[ident.name]
            yield type_ident.visit(option.type)
        elif isinstance(ident, InputObjectFieldIdent):
            data_type = schema.data_types[ident.name]
            field_type = data_type.__field_types__[ident.key]
            yield type_ident.visit(field_type)
        elif isinstance(ident, DirectiveArgIdent):
            yield NON_NULL(SCALAR('Boolean'))
        else:
            raise TypeError(repr(ident))


_directive_descriptions = {
    'include': (
        'Directs the executor to include this field or fragment '
        'only when the `if` argument is true.'
    ),
    'skip': (
        'Directs the executor to skip this field or fragment '
        'when the `if` argument is true.'
    ),
}


@listify
def directive_value_info(schema, fields, ids):
    for ident in ids:
        info = {'name': ident.name,
                'description': _directive_descriptions.get(ident.name),
                'locations': ['FIELD', 'FRAGMENT_SPREAD', 'INLINE_FRAGMENT']}
        yield [info[f.name] for f in fields]


def directive_args_link(schema, ids):
    return [[DirectiveArgIdent(ident)] for ident in ids]


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
        Link('inputFields', Sequence[TypeRef['__InputValue']],
             type_input_object_input_fields_link, requires='id'),

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
        Field('name', String, directive_value_info),
        Field('description', String, directive_value_info),
        Field('locations', Sequence[String], directive_value_info),
        Link('args', Sequence[TypeRef['__InputValue']], directive_args_link,
             requires='name'),
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
        Link('queryType', TypeRef['__Type'],
             root_schema_query_type, requires=None),
        Link('mutationType', Optional[TypeRef['__Type']],
             root_schema_mutation_type, requires=None),
        Link('subscriptionType', Optional[TypeRef['__Type']], na_maybe,
             requires=None),
        Link('directives', Sequence[TypeRef['__Directive']],
             root_schema_directives, requires=None),
    ]),
    Root([
        Link('__schema', TypeRef['__Schema'], schema_link, requires=None),
        Link('__type', Optional[TypeRef['__Type']], type_link, requires=None,
             options=[Option('name', String)]),
    ]),
])


class ValidateGraph(GraphVisitor):
    _name_re = re.compile(r'^[_a-zA-Z]\w*$', re.ASCII)

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


class BindToSchema(GraphTransformer):

    def __init__(self, schema):
        self.schema = schema
        self._processed = {}

    def visit_field(self, obj):
        field = super(BindToSchema, self).visit_field(obj)
        func = self._processed.get(obj.func)
        if func is None:
            func = self._processed[obj.func] = partial(obj.func, self.schema)
        field.func = func
        return field

    def visit_link(self, obj):
        link = super(BindToSchema, self).visit_link(obj)
        link.func = partial(link.func, self.schema)
        return link


class MakeAsync(GraphTransformer):

    def __init__(self):
        self._processed = {}

    def visit_field(self, obj):
        field = super(MakeAsync, self).visit_field(obj)
        func = self._processed.get(obj.func)
        if func is None:
            func = self._processed[obj.func] = _async_wrapper(obj.func)
        field.func = func
        return field

    def visit_link(self, obj):
        link = super(MakeAsync, self).visit_link(obj)
        link.func = _async_wrapper(link.func)
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
        root.fields.append(self.type_name_field_factory(QUERY_ROOT_NAME))
        return root

    def visit_graph(self, obj):
        graph = super(AddIntrospection, self).visit_graph(obj)
        graph.items.extend(self.introspection_graph.items)
        return graph


class SchemaInfo:

    def __init__(self, query_graph, mutation_graph=None):
        self.query_graph = query_graph
        self.data_types = query_graph.data_types
        self.mutation_graph = mutation_graph


class GraphQLIntrospection(GraphTransformer):
    """Adds GraphQL introspection into synchronous graph

    Example:

    .. code-block:: python

        from hiku.graph import apply
        from hiku.introspection.graphql import GraphQLIntrospection

        graph = apply(graph, [GraphQLIntrospection(graph)])

    """
    def __init__(self, query_graph, mutation_graph=None):
        """
        :param query_graph: graph, where Root node represents Query root
            operation type
        :param mutation_graph: graph, where Root node represents Mutation root
            operation type
        """
        self._schema = SchemaInfo(query_graph, mutation_graph)

    def __type_name__(self, node_name):
        return Field('__typename', String,
                     partial(type_name_field_func, node_name))

    def __introspection_graph__(self):
        return BindToSchema(self._schema).visit(GRAPH)

    def visit_node(self, obj):
        node = super(GraphQLIntrospection, self).visit_node(obj)
        node.fields.append(self.__type_name__(obj.name))
        return node

    def visit_root(self, obj):
        root = super(GraphQLIntrospection, self).visit_root(obj)
        root.fields.append(self.__type_name__(QUERY_ROOT_NAME))
        return root

    def visit_graph(self, obj):
        ValidateGraph.validate(obj)
        introspection_graph = self.__introspection_graph__()
        items = [self.visit(node) for node in obj.items]
        items.extend(introspection_graph.items)
        return Graph(items, data_types=obj.data_types)


class AsyncGraphQLIntrospection(GraphQLIntrospection):
    """Adds GraphQL introspection into asynchronous graph

    Example:

    .. code-block:: python

        from hiku.graph import apply
        from hiku.introspection.graphql import AsyncGraphQLIntrospection

        graph = apply(graph, [AsyncGraphQLIntrospection(graph)])

    """
    def __type_name__(self, node_name):
        return Field('__typename', String,
                     _async_wrapper(partial(type_name_field_func, node_name)))

    def __introspection_graph__(self):
        graph = super(AsyncGraphQLIntrospection, self).__introspection_graph__()
        graph = MakeAsync().visit(graph)
        return graph
