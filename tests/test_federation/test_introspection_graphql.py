from unittest.mock import ANY

from hiku.federation.endpoint import FederatedGraphQLEndpoint
from hiku.federation.engine import Engine
from hiku.executors.sync import SyncExecutor
from .utils import GRAPH
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


def _union(name, possible_types=None):
    return {
        'kind': 'UNION',
        'name': name,
        'possibleTypes': possible_types
    }


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
                _directive('skip',
                           ['FIELD', 'FRAGMENT_SPREAD', 'INLINE_FRAGMENT'] ,
                           [_ival('if', _non_null(_BOOL), description=ANY)]
                           ),
                _directive('include',
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
            'types': SCALARS + types,
        }
    }


SCALARS = [
    _type('String', 'SCALAR'),
    _type('Int', 'SCALAR'),
    _type('Boolean', 'SCALAR'),
    _type('Float', 'SCALAR'),
    _type('Any', 'SCALAR'),
]


def execute(graph, query_string):
    graphql_endpoint = FederatedGraphQLEndpoint(
        Engine(SyncExecutor()),
        graph,
    )

    return graphql_endpoint.dispatch(query_string)


def introspect(query_graph, ):
    return execute(query_graph, {'query': INTROSPECTION_QUERY})


def execute_v2(graph, query_string):
    graphql_endpoint = FederatedGraphQLEndpoint(
        Engine(SyncExecutor(), enable_v2=True),
        graph,
    )

    return graphql_endpoint.dispatch(query_string)


def introspect_v2(query_graph):
    return execute_v2(query_graph, {'query': INTROSPECTION_QUERY})


def test_federated_introspection_v1():
    exp = _schema([
        _type('Order', 'OBJECT', fields=[
            _field('cartId', _non_null(_INT)),
            _field('cart', _non_null(_obj('Cart'))),
        ]),
        _type('Cart', 'OBJECT', fields=[
            _field('id', _non_null(_INT)),
            _field('status', _non_null(_obj('Status'))),
        ]),
        _type('Query', 'OBJECT', fields=[
            _field('order', _obj('Order'), args=[
                _ival(
                    'id',
                    _non_null(_INT),
                    defaultValue=ANY
                ),
            ]),
            _field(
                '_entities',
                _seq_of_nullable(
                    _union('_Entity', [_obj('Order'), _obj('Cart')])
                ),
                args=[
                    _ival(
                        'representations',
                        _seq_of(_type('_Any', 'SCALAR')),
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
        _type('_Any', 'SCALAR'),
        _type('_FieldSet', 'SCALAR'),
        _type('_Entity', 'UNION', possibleTypes=[
            _obj('Order'), _obj('Cart')
        ]),
        _type('_Service', 'OBJECT', fields=[
            _field('sdl', _type('String', 'SCALAR')),
        ]),
    ])
    got = introspect(GRAPH)
    assert exp == got['data']


def test_federated_introspection_v2():
    exp = _schema([
        _type('Order', 'OBJECT', fields=[
            _field('cartId', _non_null(_INT)),
            _field('cart', _non_null(_obj('Cart'))),
        ]),
        _type('Cart', 'OBJECT', fields=[
            _field('id', _non_null(_INT)),
            _field('status', _non_null(_obj('Status'))),
        ]),
        _type('Query', 'OBJECT', fields=[
            _field('order', _obj('Order'), args=[
                _ival(
                    'id',
                    _non_null(_INT),
                    defaultValue=ANY
                ),
            ]),
            _field(
                '_entities',
                _seq_of_nullable(
                    _union('_Entity', [_obj('Order'), _obj('Cart')])
                ),
                args=[
                    _ival(
                        'representations',
                        _seq_of(_type('_Any', 'SCALAR')),
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
        _type('_Any', 'SCALAR'),
        _type('_FieldSet', 'SCALAR'),
        _type('_Entity', 'UNION', possibleTypes=[
            _obj('Order'), _obj('Cart')
        ]),
        _type('_Service', 'OBJECT', fields=[
            _field('sdl', _type('String', 'SCALAR')),
        ]),
    ])
    got = introspect_v2(GRAPH)
    assert exp == got['data']
