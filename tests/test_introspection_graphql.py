from hiku.graph import Graph, Root, Field, Node, Link, apply, Option
from hiku.types import String, Integer, Sequence, TypeRef, Boolean, Float, Any
from hiku.types import Optional
from hiku.result import denormalize
from hiku.engine import Engine
from hiku.sources.graph import SubGraph
from hiku.executors.sync import SyncExecutor
from hiku.validate.query import validate
from hiku.readers.graphql import read
from hiku.introspection.graphql import GraphQLIntrospection


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
        Field('yari', Boolean, flexed_sg, options=[
            Option('membuka', Sequence[String], default=['frayed']),
            Option('modist', Optional[Integer], default=None,
                   description='callow'),
        ]),
    ]),
    Node('decian', [
        Field('dogme', Integer, field_func),
        Link('clarkia', Sequence[TypeRef['flexed']], link_func,
             requires=None),
    ]),
    Root([
        Field('cowered', String, field_func),
        Field('entero', Float, field_func),
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
_FLOAT = {'kind': 'SCALAR', 'name': 'Float', 'ofType': None}


def _obj(name):
    return {'kind': 'OBJECT', 'name': name, 'ofType': None}


def _seq_of(_type):
    return {'kind': 'NON_NULL', 'name': None,
            'ofType': {'kind': 'LIST', 'name': None,
                       'ofType': {'kind': 'NON_NULL', 'name': None,
                                  'ofType': _type}}}


RESULT = {
    '__schema': {
        'queryType': {'name': 'Root'},
        'mutationType': None,
        'directives': [],
        'types': [
            {
                'name': 'String',
                'kind': 'SCALAR',
                'fields': [],
                'description': None,
                'enumValues': [],
                'inputFields': [],
                'interfaces': [],
                'possibleTypes': [],
            },
            {
                'name': 'Int',
                'kind': 'SCALAR',
                'fields': [],
                'description': None,
                'enumValues': [],
                'inputFields': [],
                'interfaces': [],
                'possibleTypes': [],
            },
            {
                'name': 'Boolean',
                'kind': 'SCALAR',
                'fields': [],
                'description': None,
                'enumValues': [],
                'inputFields': [],
                'interfaces': [],
                'possibleTypes': [],
            },
            {
                'name': 'Float',
                'kind': 'SCALAR',
                'fields': [],
                'description': None,
                'enumValues': [],
                'inputFields': [],
                'interfaces': [],
                'possibleTypes': [],
            },
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
                        'args': [
                            {
                                'name': 'membuka',
                                'type': _seq_of(_STR),
                                'description': None,
                                'defaultValue': '["frayed"]',
                            },
                            {
                                'name': 'modist',
                                'type': _INT,
                                'description': 'callow',
                                'defaultValue': 'null',
                            },
                        ],
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
                        'type': _seq_of(_obj('flexed')),
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
                        'name': 'entero',
                        'type': _non_null(_FLOAT),
                        'description': None,
                        'isDeprecated': False,
                        'deprecationReason': None,
                        'args': [],
                    },
                    {
                        'name': 'toma',
                        'type': _seq_of(_obj('decian')),
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


def test_typename():
    graph = apply(GRAPH, [GraphQLIntrospection()])
    assert graph.root.fields_map['__typename'].type is String
    assert graph.root.fields_map['__typename'].func([None]) == ['Root']

    decian = graph.nodes_map['decian']
    assert decian.fields_map['__typename'].type is String
    assert decian.fields_map['__typename'].func([None]) == ['decian']

    flexed = graph.nodes_map['flexed']
    assert flexed.fields_map['__typename'].type is String
    assert flexed.fields_map['__typename'].func([None]) == ['flexed']


def introspect(graph):
    engine = Engine(SyncExecutor())
    graph = apply(graph, [GraphQLIntrospection()])

    query = read(QUERY)
    errors = validate(graph, query)
    assert not errors

    norm_result = engine.execute(graph, query)
    return denormalize(graph, norm_result, query)


def test_introspection_query():
    assert introspect(GRAPH) == RESULT


def test_unsupported_field():
    result = introspect(Graph([Root([Field('fall', Optional[Any], field_func),
                                     Field('huss', Integer, field_func)])]))

    assert result['__schema']['types'][-1]['name'] == 'Root'
    assert [f['name'] for f in result['__schema']['types'][-1]['fields']] == \
           ['huss']


def test_unsupported_option():
    result = introspect(Graph([Root([Field('huke', Integer, field_func,
                                           options=[Option('orel',
                                                           Optional[Any])]),
                                     Field('terapin', Integer, field_func)])]))

    assert result['__schema']['types'][-1]['name'] == 'Root'
    assert [f['name'] for f in result['__schema']['types'][-1]['fields']] == \
           ['terapin']
