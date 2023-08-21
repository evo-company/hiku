from unittest.mock import ANY

from hiku.federation.directive import Key
from hiku.federation.endpoint import FederatedGraphQLEndpoint
from hiku.federation.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.federation.graph import FederatedNode, Graph
from hiku.graph import Field, Root
from hiku.types import Integer, TypeRef
from .utils import GRAPH
from ..test_introspection_graphql import SCALARS
from ..utils import INTROSPECTION_QUERY


def _noop():
    raise NotImplementedError


def _non_null(t):
    return {'kind': 'NON_NULL', 'name': None, 'ofType': t}


def _scalar(name):
    return {'kind': 'SCALAR', 'name': name, 'ofType': None}


_INT = _scalar('Int')
_STR = _scalar('String')
_BOOL = _scalar('Boolean')
_FLOAT = _scalar('Float')
_ANY = _scalar('Any')
_FIELDSET = _scalar('_FieldSet')


def _obj(name):
    return {'kind': 'OBJECT', 'name': name, 'ofType': None}


def _iobj(name):
    return {'kind': 'INPUT_OBJECT', 'name': name, 'ofType': None}


def _union(name):
    return {'kind': 'UNION', 'name': name, 'ofType': None}


def _seq_of(_type):
    return {'kind': 'NON_NULL', 'name': None,
            'ofType': {'kind': 'LIST', 'name': None,
                       'ofType': {'kind': 'NON_NULL', 'name': None,
                                  'ofType': _type}}}


def _seq_of_nullable(_type):
    return {'kind': 'NON_NULL', 'name': None,
            'ofType': {'kind': 'LIST', 'name': None,
                       'ofType': _type}}


def _field(name, type_, **kwargs):
    data = {
        'args': [],
        'deprecationReason': None,
        'description': None,
        'isDeprecated': False,
        'name': name,
        'type': type_
    }
    data.update(kwargs)
    return data


def _type(name, kind, **kwargs):
    data = {
        'description': None,
        'enumValues': [],
        'fields': [],
        'inputFields': [],
        'interfaces': [],
        'kind': kind,
        'name': name,
        'possibleTypes': [],
    }
    data.update(**kwargs)
    return data


def _directive(name, locs, args=None):
    return {
        'name': name,
        'description': ANY,
        'locations': locs,
        'args': args or [],
    }


def _ival(name, type_, **kwargs):
    data = {
        'name': name,
        'type': type_,
        'description': None,
        'defaultValue': None,
    }
    data.update(kwargs)
    return data


def _schema(types, with_mutation=False) -> dict:
    names = [t['name'] for t in types]
    assert 'Query' in names, names
    return {
        '__schema': {
            'directives': [
                _directive(
                    'skip',
                    ['FIELD', 'FRAGMENT_SPREAD', 'INLINE_FRAGMENT'] ,
                    [_ival('if', _non_null(_BOOL), description=ANY)]
                ),
                _directive(
                    'include',
                    ['FIELD', 'FRAGMENT_SPREAD', 'INLINE_FRAGMENT'], [
                        _ival('if', _non_null(_BOOL), description=ANY),
                    ]),
                _directive('deprecated', ['FIELD_DEFINITION', 'ENUM_VALUE'], [
                    _ival('reason', _STR, description=ANY)
                ]),
                _directive('cached', ['FIELD', 'FRAGMENT_SPREAD', 'INLINE_FRAGMENT'], [
                    _ival('ttl', _non_null(_INT), description=ANY)
                ]),
            ],
            'mutationType': {'name': 'Mutation'} if with_mutation else None,
            'queryType': {'name': 'Query'},
            'types': SCALARS + types
        }
    }


def execute(graph, query_string):
    graphql_endpoint = FederatedGraphQLEndpoint(
        Engine(SyncExecutor()),
        graph,
        federation_version=1
    )

    return graphql_endpoint.dispatch(query_string)


def introspect(query_graph, ):
    return execute(query_graph, {'query': INTROSPECTION_QUERY})


def execute_v2(graph, query_string):
    graphql_endpoint = FederatedGraphQLEndpoint(
        Engine(SyncExecutor()),
        graph,
    )

    return graphql_endpoint.dispatch(query_string)


def introspect_v2(query_graph):
    return execute_v2(query_graph, {'query': INTROSPECTION_QUERY})


def test_federated_introspection_v1():
    exp = _schema([
        _type('Cart', 'OBJECT', fields=[
            _field('id', _non_null(_INT)),
            _field('status', _non_null(_obj('Status'))),
        ]),
        _type('Query', 'OBJECT', fields=[
            _field('cart', _obj('Cart'), args=[
                _ival(
                    'id',
                    _non_null(_INT),
                    defaultValue=ANY
                ),
            ]),
            _field(
                '_entities',
                _seq_of_nullable(
                    _union('_Entity')
                ),
                args=[
                    _ival(
                        'representations',
                        _seq_of(_scalar('_Any')),
                        defaultValue=ANY
                    ),
                ]
            ),
            _field(
                '_service',
                _non_null(_obj('_Service')),
            ),
        ]),
        _type('Status', 'OBJECT', fields=[
            _field('id', _non_null(_INT)),
            _field('title', _non_null(_STR)),
        ]),
        _type('IOStatus', 'INPUT_OBJECT', inputFields=[
            _ival('id', _non_null(_INT)),
            _ival('title', _non_null(_STR)),
        ]),
        _type('_Service', 'OBJECT', fields=[
            _field('sdl', _non_null(_scalar('String'))),
        ]),
        _type('_Entity', 'UNION', possibleTypes=[
            _obj('Cart')
        ]),
        _type('_Any', 'SCALAR'),
        _type('_FieldSet', 'SCALAR'),
        _type('link__Import', 'SCALAR'),
    ])
    got = introspect(GRAPH)
    assert exp == got['data']


def test_federated_introspection_v2():
    exp = _schema([
        _type('Cart', 'OBJECT', fields=[
            _field('id', _non_null(_INT)),
            _field('status', _non_null(_obj('Status'))),
        ]),
        _type('Query', 'OBJECT', fields=[
            _field('cart', _obj('Cart'), args=[
                _ival(
                    'id',
                    _non_null(_INT),
                    defaultValue=ANY
                ),
            ]),
            _field(
                '_entities',
                _seq_of_nullable(
                    _union('_Entity')
                ),
                args=[
                    _ival(
                        'representations',
                        _seq_of(_scalar('_Any')),
                        defaultValue=ANY
                    ),
                ]
            ),
            _field(
                '_service',
                _non_null(_obj('_Service')),
            ),
        ]),
        _type('Status', 'OBJECT', fields=[
            _field('id', _non_null(_INT)),
            _field('title', _non_null(_STR)),
        ]),
        _type('IOStatus', 'INPUT_OBJECT', inputFields=[
            _ival('id', _non_null(_INT)),
            _ival('title', _non_null(_STR)),
        ]),
        _type('_Service', 'OBJECT', fields=[
            _field('sdl', _non_null(_scalar('String'))),
        ]),
        _type('_Entity', 'UNION', possibleTypes=[
            _obj('Cart')
        ]),
        _type('_Any', 'SCALAR'),
        _type('_FieldSet', 'SCALAR'),
        _type('link__Import', 'SCALAR'),
    ])
    got = introspect_v2(GRAPH)
    assert exp == got['data']


def test_introspection_partial_query():
    query = """
    query IntrospectionQuery {
        __schema {
            queryType { name }
        }
    }
    """
    got = execute_v2(GRAPH, {'query': query})
    assert got['data'] == {
        '__schema': {
            'queryType': {'name': 'Query'}
        }
    }


def test_entity_type_when_no_type_has_key():
    query = """
    query IntrospectionQuery {
       __type(name: "_Entity") {
            kind
            possibleTypes {
                name
            }
        }
    }
    """

    graph = Graph([
        FederatedNode('Cart', [
            Field('id', Integer, _noop),
        ]),
    ])
    got = execute_v2(graph, {'query': query})
    assert got['data'] == {
        '__type': None
    }


def test_entity_type_when_type_has_key():
    query = """
    query IntrospectionQuery {
       __type(name: "_Entity") {
            kind
            possibleTypes {
                name
            }
        }
    }
    """

    graph = Graph([
        FederatedNode('Cart', [
            Field('id', Integer, _noop),
        ], directives=[Key('id')]),
    ])
    got = execute_v2(graph, {'query': query})
    assert got['data'] == {
        '__type': {"kind": "UNION", "possibleTypes": [{"name": "Cart"}]}
    }


def test_entities_field_when_no_type_has_key():
    query = """
    query IntrospectionQuery {
       __type(name: "Query") {
            kind
            fields { name }
        }
    }
    """

    graph = Graph([
        FederatedNode('Cart', [
            Field('id', Integer, _noop),
        ]),
        Root([
            Field('cart', TypeRef['Cart'], _noop),
        ])
    ])
    got = execute_v2(graph, {'query': query})
    assert got['data'] == {
        '__type': {
            "kind": "OBJECT",
            "fields": [{
                "name": "cart",
            }]
        }
    }


def test_entities_field_when_type_has_key():
    query = """
    query IntrospectionQuery {
       __type(name: "Query") {
            kind
            fields { name }
        }
    }
    """

    graph = Graph([
        FederatedNode('Cart', [
            Field('id', Integer, _noop),
        ], directives=[Key('id')]),
        Root([
            Field('cart', TypeRef['Cart'], _noop),
        ])
    ])
    got = execute_v2(graph, {'query': query})
    assert got['data'] == {
        '__type': {
            "kind": "OBJECT",
            "fields": [{
                "name": "cart",
            }, {
                "name": "_entities",
            }, {
                "name": "_service",
            }]
        }
    }
