from unittest import TestCase
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


_INT = {'kind': 'SCALAR', 'name': 'Int', 'ofType': None}
_STR = {'kind': 'SCALAR', 'name': 'String', 'ofType': None}
_BOOL = {'kind': 'SCALAR', 'name': 'Boolean', 'ofType': None}
_FLOAT = {'kind': 'SCALAR', 'name': 'Float', 'ofType': None}
_ANY = {'kind': 'SCALAR', 'name': 'Any', 'ofType': None}
_FIELDSET = {'kind': 'SCALAR', 'name': '_FieldSet', 'ofType': None}


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


def _field_directive(name, args):
    return {
        'name': name,
        'description': ANY,
        'locations': ['FIELD', 'FRAGMENT_SPREAD', 'INLINE_FRAGMENT'],
        'args': args,
    }


def _object_directive(name, args):
    return {
        'name': name,
        'description': ANY,
        'locations': ['OBJECT', 'INTERFACE'],
        'args': args,
    }


def _field_def_directive(name, args):
    return {
        'name': name,
        'description': ANY,
        'locations': ['FIELD_DEFINITION'],
        'args': args,
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
                _field_directive('skip', [
                    _ival('if', _non_null(_BOOL), description=ANY),
                ]),
                _field_directive('include', [
                    _ival('if', _non_null(_BOOL), description=ANY),
                ]),
                _object_directive('key', [
                    _ival('fields', _non_null(_FIELDSET), description=ANY),
                ]),
                _field_def_directive('provides', [
                    _ival('fields', _non_null(_FIELDSET), description=ANY),
                ]),
                _field_def_directive('requires', [
                    _ival('fields', _non_null(_FIELDSET), description=ANY),
                ]),
                _field_def_directive('external', []),
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


def introspect(query_graph):
    return execute(query_graph, {'query': INTROSPECTION_QUERY})


class TestFederatedGraphIntrospection(TestCase):
    def test_federated_introspection_query_entities(self):
        self.maxDiff = None
        exp = _schema([
            _type('Order', 'OBJECT', fields=[
                _field('cartId', _non_null(_INT)),
                _field('cart', _non_null(_obj('Cart'))),
            ]),
            _type('Cart', 'OBJECT', fields=[
                _field('id', _non_null(_INT)),
                _field('status', _non_null(_obj('Status'))),
                _field('items', _seq_of(_obj('CartItem'))),
            ]),
            _type('CartItem', 'OBJECT', fields=[
                _field('id', _non_null(_INT)),
                _field('cart_id', _non_null(_INT)),
                _field('name', _non_null(_STR)),
                _field('photo', _STR, args=[
                    _ival(
                        'width',
                        _non_null(_INT),
                        defaultValue=ANY
                    ),
                    _ival(
                        'height',
                        _non_null(_INT),
                        defaultValue=ANY
                    ),
                ]),
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
        self.assertEqual(exp, got['data'])
