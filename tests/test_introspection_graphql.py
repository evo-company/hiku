from hiku.graph import Graph, Root, Field, Node, Link
from hiku.types import String, Integer, Sequence, TypeRef, Boolean
from hiku.result import denormalize
from hiku.engine import Engine
from hiku.expr.core import S
from hiku.sources.graph import SubGraph, Expr
from hiku.executors.sync import SyncExecutor
from hiku.readers.graphql import read
from hiku.introspection.graphql import add_introspection


def field_func():
    raise NotImplementedError


def link_func():
    raise NotImplementedError


_GRAPH = Graph([
    Node('flexed', [
        Field('yari', Boolean, field_func),
    ]),
])

flexed_sg = SubGraph(_GRAPH, 'flexed')

GRAPH = Graph([
    Node('flexed', [
        Expr('yari', flexed_sg, Boolean, S.this.yari),
    ]),
    Node('decian', [
        Field('dogme', Integer, field_func),
        Link('clarkia', Sequence[TypeRef['flexed']], link_func,
             requires=None),
    ]),
    Root([
        Field('cowered', String, field_func),
        Link('toma', Sequence[TypeRef['decian']], link_func,
             requires=None),
    ]),
])


QUERY = """
query IntrospectionQuery {
    __schema {
        queryType { name }
        mutationType { name }
        types { ...FullType }
        directives {
            name
            description
            locations
            args { ...InputValue }
        }
    }
}

fragment FullType on __Type {
    kind
    name
    description
    fields(includeDeprecated: true) {
        name
        description
        args { ...InputValue }
        type { ...TypeRef }
        isDeprecated
        deprecationReason
    }
    inputFields { ...InputValue }
    interfaces { ...TypeRef }
    enumValues(includeDeprecated: true) {
        name
        description
        isDeprecated
        deprecationReason
    }
    possibleTypes { ...TypeRef }
}

fragment InputValue on __InputValue {
    name
    description
    type { ...TypeRef }
    defaultValue
}

fragment TypeRef on __Type {
    kind
    name
    ofType {
        kind
        name
        ofType {
            kind
            name
            ofType {
                kind
                name
                ofType {
                    kind
                    name
                    ofType {
                    kind
                    name
                        ofType {
                        kind
                        name
                            ofType {
                                kind
                                name
                            }
                        }
                    }
                }
            }
        }
    }
}
"""


def _non_null(t):
    return {'kind': 'NON_NULL', 'name': None, 'ofType': t}


_INT = {'kind': 'SCALAR', 'name': 'Int', 'ofType': None}
_STR = {'kind': 'SCALAR', 'name': 'String', 'ofType': None}
_BOOL = {'kind': 'SCALAR', 'name': 'Boolean', 'ofType': None}


def _seq_of(name):
    return {'kind': 'NON_NULL', 'name': None,
            'ofType': {'kind': 'LIST', 'name': None,
                       'ofType': {'kind': 'NON_NULL', 'name': None,
                                  'ofType': {'kind': 'OBJECT', 'name': name,
                                             'ofType': None}}}}


RESULT = {
    '__schema': {
        'queryType': {'name': 'Root'},
        'mutationType': None,
        'directives': [],
        'types': [
            {
                'name': 'flexed',
                'kind': 'OBJECT',
                'fields': [
                    {
                        'name': 'yari',
                        'type': _non_null(_BOOL),
                        'description': None,
                        'isDeprecated': False,
                        'deprecationReason': None,
                        'args': [],
                    },
                ],
                'description': None,
                'enumValues': [],
                'inputFields': [],
                'interfaces': [],
                'possibleTypes': [],
            },
            {
                'name': 'decian',
                'kind': 'OBJECT',
                'fields': [
                    {
                        'name': 'dogme',
                        'type': _non_null(_INT),
                        'description': None,
                        'isDeprecated': False,
                        'deprecationReason': None,
                        'args': [],
                    },
                    {
                        'name': 'clarkia',
                        'type': _seq_of('flexed'),
                        'description': None,
                        'isDeprecated': False,
                        'deprecationReason': None,
                        'args': [],
                    },
                ],
                'description': None,
                'enumValues': [],
                'inputFields': [],
                'interfaces': [],
                'possibleTypes': [],
            },
            {
                'name': 'Root',
                'kind': 'OBJECT',
                'fields': [
                    {
                        'name': 'cowered',
                        'type': _non_null(_STR),
                        'description': None,
                        'isDeprecated': False,
                        'deprecationReason': None,
                        'args': [],
                    },
                    {
                        'name': 'toma',
                        'type': _seq_of('decian'),
                        'description': None,
                        'isDeprecated': False,
                        'deprecationReason': None,
                        'args': [],
                    },
                ],
                'description': None,
                'enumValues': [],
                'inputFields': [],
                'interfaces': [],
                'possibleTypes': [],
            },
        ],
    },
}


def test_graph_transformer():
    old_flexed = GRAPH.nodes_map['flexed']
    graph = add_introspection(GRAPH)
    new_flexed = graph.nodes_map['flexed']

    old_yari = old_flexed.fields_map['yari']
    new_yari = new_flexed.fields_map['yari']

    assert isinstance(new_yari, Expr)
    assert old_yari is not new_yari
    assert old_yari.name == new_yari.name
    assert old_yari.type is new_yari.type
    assert old_yari.func is new_yari.func
    assert old_yari.expr is new_yari.expr


def test_typename():
    graph = add_introspection(GRAPH)
    assert graph.root.fields_map['__typename'].type is String
    assert graph.root.fields_map['__typename'].func([None]) == ['Root']

    decian = graph.nodes_map['decian']
    assert decian.fields_map['__typename'].type is String
    assert decian.fields_map['__typename'].func([None]) == ['decian']

    flexed = graph.nodes_map['flexed']
    assert flexed.fields_map['__typename'].type is String
    assert flexed.fields_map['__typename'].func([None]) == ['flexed']


def test_introspection_query():
    engine = Engine(SyncExecutor())
    graph = add_introspection(GRAPH)
    query = read(QUERY)
    norm_result = engine.execute(graph, query)
    result = denormalize(graph, norm_result, query)
    assert result == RESULT
