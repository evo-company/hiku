from hiku.graph import Graph, Root, Field, Node, Link, apply, Option
from hiku.types import String, Integer, Sequence, TypeRef, Boolean, Float, Any
from hiku.types import Optional, Record
from hiku.result import denormalize
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.validate.query import validate
from hiku.readers.graphql import read
from hiku.introspection.graphql import GraphQLIntrospection


def _noop():
    raise NotImplementedError


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


def _iface(name):
    return {'kind': 'INTERFACE', 'name': name, 'ofType': None}


def _seq_of(_type):
    return {'kind': 'NON_NULL', 'name': None,
            'ofType': {'kind': 'LIST', 'name': None,
                       'ofType': {'kind': 'NON_NULL', 'name': None,
                                  'ofType': _type}}}


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


def _schema(types):
    names = [t['name'] for t in types]
    assert 'Root' in names, names
    return {
        '__schema': {
            'directives': [],
            'mutationType': None,
            'queryType': {'name': 'Root'},
            'types': SCALARS + types,
        }
    }


def _arg(name, type_, **kwargs):
    data = {
        'name': name,
        'type': type_,
        'description': None,
        'defaultValue': 'null',
    }
    data.update(kwargs)
    return data


SCALARS = [
    _type('String', 'SCALAR'),
    _type('Int', 'SCALAR'),
    _type('Boolean', 'SCALAR'),
    _type('Float', 'SCALAR'),
]


def introspect(graph):
    engine = Engine(SyncExecutor())
    graph = apply(graph, [GraphQLIntrospection()])

    query = read(QUERY)
    errors = validate(graph, query)
    assert not errors

    norm_result = engine.execute(graph, query)
    return denormalize(graph, norm_result, query)


def test_introspection_query():
    graph = Graph([
        Node('flexed', [
            Field('yari', Boolean, _noop, options=[
                Option('membuka', Sequence[String], default=['frayed']),
                Option('modist', Optional[Integer], default=None,
                       description='callow'),
            ]),
        ]),
        Node('decian', [
            Field('dogme', Integer, _noop),
            Link('clarkia', Sequence[TypeRef['flexed']], _noop, requires=None),
        ]),
        Root([
            Field('cowered', String, _noop),
            Field('entero', Float, _noop),
            Link('toma', Sequence[TypeRef['decian']], _noop, requires=None),
        ]),
    ])

    assert introspect(graph) == _schema([
        _type('flexed', 'OBJECT', fields=[
            _field('yari', _non_null(_BOOL), args=[
                _arg('membuka', _seq_of(_STR), defaultValue='["frayed"]'),
                _arg('modist', _INT, description='callow'),
            ]),
        ]),
        _type('decian', 'OBJECT', fields=[
            _field('dogme', _non_null(_INT)),
            _field('clarkia', _seq_of(_obj('flexed'))),
        ]),
        _type('Root', 'OBJECT', fields=[
            _field('cowered', _non_null(_STR)),
            _field('entero', _non_null(_FLOAT)),
            _field('toma', _seq_of(_obj('decian'))),
        ]),
    ])


def test_unsupported_field():
    graph = Graph([
        Root([
            Field('fall', Optional[Any], _noop),
            Field('bayman', Optional[Record[{'foo': Optional[Integer]}]],
                  _noop),
            Field('huss', Integer, _noop),
        ]),
    ])
    assert introspect(graph) == _schema([
        _type('Root', 'OBJECT', fields=[
            _field('huss', _non_null(_INT)),
        ]),
    ])


def test_unsupported_option():
    graph = Graph([
        Root([
            Field('huke', Integer, _noop,
                  options=[Option('orel', Optional[Any])]),
            Field('terapin', Integer, _noop),
        ]),
    ])
    assert introspect(graph) == _schema([
        _type('Root', 'OBJECT', fields=[
            _field('terapin', _non_null(_INT)),
        ]),
    ])


def test_data_types():
    data_types = {
        'Foo': Record[{
            'bar': Integer,
            'invalid_type': Any,
            'invalid-name': Integer,
        }],
    }
    graph = Graph([Root([
        Field('foo', TypeRef['Foo'], _noop),
    ])], data_types)
    assert introspect(graph) == _schema([
        _type('Root', 'OBJECT', fields=[
            _field('foo', _non_null(_iface('Foo'))),
        ]),
        _type('Foo', 'INTERFACE', fields=[
            _field('bar', _non_null(_INT)),
        ]),
        _type('IFoo', 'INPUT_OBJECT', fields=[
            _field('bar', _non_null(_INT)),
        ]),
    ])
