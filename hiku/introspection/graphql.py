import re

from itertools import chain
from functools import partial
from collections import namedtuple, OrderedDict

from ..graph import Graph, Root, Node, Link, Option, Field, Nothing
from ..graph import GraphTransformer
from ..types import TypeRef, String, Sequence, Boolean, Optional, TypeVisitor
from ..compat import text_type, async_wrapper


LIST = namedtuple('LIST', 'of_type')
NON_NULL = namedtuple('NON_NULL', 'of_type')

FieldIdent = namedtuple('FieldIdent', 'node, name')
ArgumentIdent = namedtuple('ArgumentIdent', 'node, field, name')

NAME_RE = re.compile('^[a-zA-Z]\w*$')

ROOT_NAME = 'Root'


class TypeIdent(TypeVisitor):

    def visit_sequence(self, obj):
        return NON_NULL(LIST(self.visit(obj.__item_type__)))

    def visit_optional(self, obj):
        return self.visit(obj.__type__).of_type

    def visit_typeref(self, obj):
        return NON_NULL(obj.__type_name__)

    def visit_string(self, obj):
        return NON_NULL('String')

    def visit_integer(self, obj):
        return NON_NULL('Int')

    def visit_boolean(self, obj):
        return NON_NULL('Boolean')


def not_implemented(*args, **kwargs):
    raise NotImplementedError


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


def type_link(graph, options):
    name = options['name']
    if name in _nodes_map(graph):
        return name
    else:
        return Nothing


def types_link(graph):
    return [n for n in _nodes_map(graph) if NAME_RE.match(n)]


def type_info(graph, fields, ids):
    nodes_map = _nodes_map(graph)
    for ident in ids:
        if ident in nodes_map:
            node = nodes_map[ident]
            info = {'id': ident,
                    'kind': 'OBJECT',
                    'name': ident,
                    'description': node.description}
        elif isinstance(ident, NON_NULL):
            info = {'id': ident,
                    'kind': 'NON_NULL'}
        elif isinstance(ident, LIST):
            info = {'id': ident,
                    'kind': 'LIST'}
        else:
            assert ident in {'String', 'Int', 'Boolean'}, ident
            info = {'id': ident,
                    'name': ident,
                    'kind': 'SCALAR'}
        yield [info.get(f.name) for f in fields]


def type_fields_link(graph, ids, options):
    nodes_map = _nodes_map(graph)
    for ident in ids:
        node = nodes_map[ident]
        field_idents = [FieldIdent(ident, f.name) for f in node.fields
                        if NAME_RE.match(f.name) and f.type is not None]
        if not field_idents:
            raise TypeError('Node "{}" does not contain any typed field, which '
                            'is not acceptable for GraphQL in order to define '
                            'schema type'.format(ident))
        yield field_idents


def type_of_type_link(graph, ids):
    for ident in ids:
        if isinstance(ident, (NON_NULL, LIST)):
            yield ident.of_type
        else:
            yield Nothing


def field_info(graph, fields, ids):
    nodes_map = _nodes_map(graph)
    for ident in ids:
        node = nodes_map[ident.node]
        field = node.fields_map[ident.name]
        info = {'id': ident,
                'name': field.name,
                'description': field.description,
                'isDeprecated': False,
                'deprecationReason': None}
        yield [info[f.name] for f in fields]


def field_type_link(graph, ids):
    nodes_map = _nodes_map(graph)
    type_ident = TypeIdent()
    for ident in ids:
        node = nodes_map[ident.node]
        field = node.fields_map[ident.name]
        yield type_ident.visit(field.type)


def field_args_link(graph, ids):
    nodes_map = _nodes_map(graph)
    for ident in ids:
        node = nodes_map[ident.node]
        field = node.fields_map[ident.name]
        yield [ArgumentIdent(ident.node, field.name, option.name)
               for option in field.options
               if NAME_RE.match(option.name) and option.type is not None]


def input_value_info(graph, fields, ids):
    nodes_map = _nodes_map(graph)
    for ident in ids:
        node = nodes_map[ident.node]
        field = node.fields_map[ident.field]
        option = field.options_map[ident.name]
        info = {'id': ident,
                'name': option.name,
                'description': None,
                'defaultValue': (None if option.default is Nothing
                                 else text_type(option.default))}
        yield [info[f.name] for f in fields]


def input_value_type_link(graph, ids):
    nodes_map = _nodes_map(graph)
    type_ident = TypeIdent()
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
             requires='name',
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
    Root([
        Node('__schema', [
            Link('types', Sequence[TypeRef['__Type']], types_link,
                 requires=None),
            Link('queryType', TypeRef['__Type'], lambda graph: ROOT_NAME,
                 requires=None),
            Link('directives', Sequence[TypeRef['__Directive']], na_many,
                 requires=None),
            Link('mutationType', Optional[TypeRef['__Type']], na_maybe,
                 requires=None),
            Link('subscriptionType', Optional[TypeRef['__Type']], na_maybe,
                 requires=None),
        ]),
        Link('__type', Optional[TypeRef['__Type']], type_link, requires=None,
             options=[Option('name', String)]),
    ]),
])


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
        introspection_graph = self.__introspection_graph__(obj)
        items = [self.visit(node) for node in obj.items]
        items.extend(introspection_graph.items)
        return Graph(items)


class AsyncGraphQLIntrospection(GraphQLIntrospection):

    def __type_name__(self, node_name):
        return Field('__typename', String,
                     async_wrapper(partial(type_name_field_func, node_name)))

    def __introspection_graph__(self, graph):
        introspection_graph = BindToGraph(graph).visit(GRAPH)
        introspection_graph = MakeAsync().visit(introspection_graph)
        return introspection_graph
