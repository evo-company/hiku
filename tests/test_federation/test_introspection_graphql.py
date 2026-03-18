from unittest.mock import ANY

from graphql import get_introspection_query

from hiku.executors.sync import SyncExecutor
from hiku.federation.directive import Key
from hiku.federation.graph import FederatedNode, Graph
from hiku.federation.schema import Schema
from hiku.graph import Field, Root
from hiku.types import Integer, TypeRef
from .utils import GRAPH
from ..test_introspection_graphql import (
    SCALARS,
    _INT,
    _STR,
    _BOOL,
    _noop,
    _non_null,
    _scalar,
    _obj,
    _union,
    _seq_of,
    _field,
    _type,
    _directive,
    _ival,
)


_FIELDSET = _scalar('_FieldSet')


def _seq_of_nullable(_type):
    return {'kind': 'NON_NULL', 'name': None,
            'ofType': {'kind': 'LIST', 'name': None,
                       'ofType': _type}}


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
                _directive('deprecated', [
                    'FIELD_DEFINITION',
                    'ARGUMENT_DEFINITION',
                    'INPUT_FIELD_DEFINITION',
                    'ENUM_VALUE',
                ], [
                    _ival('reason', _STR, description=ANY)
                ]),
                _directive('cached', ['FIELD', 'FRAGMENT_SPREAD', 'INLINE_FRAGMENT'], [
                    _ival('ttl', _non_null(_INT), description=ANY)
                ]),
            ],
            'mutationType': {'name': 'Mutation'} if with_mutation else None,
            'queryType': {'name': 'Query'},
            'subscriptionType': None,
            'types': SCALARS + types
        }
    }


def execute(graph, query_string):
    schema = Schema(
        SyncExecutor(),
        graph,
        federation_version=1
    )

    return schema.execute_sync(query_string)


def introspect(query_graph, ):
    return execute(
        query_graph,
        get_introspection_query(
            input_value_deprecation=True,
            directive_is_repeatable=True,
        ),
    )


def execute_v2(graph, query_string):
    schema = Schema(
        SyncExecutor(),
        graph,
    )

    return schema.execute_sync(query_string)


def introspect_v2(query_graph):
    return execute_v2(
        query_graph,
        get_introspection_query(
            input_value_deprecation=True,
            directive_is_repeatable=True,
        ),
    )


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
    assert exp == got.data


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
    assert exp == got.data


def test_introspection_partial_query():
    query = """
    query IntrospectionQuery {
        __schema {
            queryType { name }
        }
    }
    """
    got = execute_v2(GRAPH, query)
    assert got.data == {
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
    got = execute_v2(graph, query)
    assert got.data == {
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
    got = execute_v2(graph, query)
    assert got.data == {
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
    got = execute_v2(graph, query)
    assert got.data == {
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
    got = execute_v2(graph, query)
    assert got.data == {
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
