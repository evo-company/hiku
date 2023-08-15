import enum

from typing import Dict, List
from unittest.mock import ANY

import pytest
from hiku.endpoint.graphql import GraphQLEndpoint

from hiku.enum import Enum

from hiku.directives import Deprecated, Location, SchemaDirective, schema_directive
from hiku.graph import Graph, Interface, Root, Field, Node, Link, Union, apply, Option
from hiku.scalar import Scalar
from hiku.types import EnumRef, InterfaceRef, String, Integer, Sequence, TypeRef, Boolean, Float, Any, UnionRef
from hiku.types import Optional, Record
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.introspection.graphql import GraphQLIntrospection
from tests.utils import INTROSPECTION_QUERY


def _noop():
    raise NotImplementedError


def _non_null(t):
    return {'kind': 'NON_NULL', 'name': None, 'ofType': t}


_INT = {'kind': 'SCALAR', 'name': 'Int', 'ofType': None}
_STR = {'kind': 'SCALAR', 'name': 'String', 'ofType': None}
_BOOL = {'kind': 'SCALAR', 'name': 'Boolean', 'ofType': None}
_FLOAT = {'kind': 'SCALAR', 'name': 'Float', 'ofType': None}
_ANY = {'kind': 'SCALAR', 'name': 'Any', 'ofType': None}


def _obj(name):
    return {'kind': 'OBJECT', 'name': name, 'ofType': None}


def _union(name):
    return {
        'kind': 'UNION',
        'name': name,
        'ofType': None
    }


def _interface(name):
    return {
        'kind': 'INTERFACE',
        'name': name,
        'ofType': None
    }


def _enum(name):
    return {
        'kind': 'ENUM',
        'name': name,
        'ofType': None
    }


def _scalar(name):
    return {
        'kind': 'SCALAR',
        'name': name,
        'ofType': None
    }


def _iobj(name):
    return {'kind': 'INPUT_OBJECT', 'name': name, 'ofType': None}


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


def _enum_value(name, **kwargs):
    data = {
        'deprecationReason': None,
        'description': None,
        'isDeprecated': False,
        'name': name,
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


def _directive(name, locs, args = None):
    return {
        'name': name,
        'description': ANY,
        'locations': locs,
        'args': args or [],
    }


def _field_enum_directive(name, args):
    return {
        'name': name,
        'description': ANY,
        'locations': ['FIELD_DEFINITION', 'ENUM_VALUE'],
        'args': args,
    }


def _schema(types, directives: Optional[List[Dict]] = None, with_mutation=False):
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
              _directive(
                  'deprecated', ['FIELD_DEFINITION', 'ENUM_VALUE'], [
                      _ival('reason', _STR, description=ANY)
                  ]),
              _directive(
                  'cached', ['FIELD', 'FRAGMENT_SPREAD', 'INLINE_FRAGMENT'], [
                      _ival('ttl', _non_null(_INT), description=ANY)
                  ]),
            ] + (directives or []),
            'mutationType': {'name': 'Mutation'} if with_mutation else None,
            'queryType': {'name': 'Query'},
            'types': SCALARS + types
        }
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


SCALARS = [
    _type('String', 'SCALAR'),
    _type('Int', 'SCALAR'),
    _type('Boolean', 'SCALAR'),
    _type('Float', 'SCALAR'),
    _type('Any', 'SCALAR'),
    _type('ID', 'SCALAR'),
]


def execute(query_str, query_graph, mutation_graph=None):
    engine = Engine(SyncExecutor())
    endpoint = GraphQLEndpoint(engine, query_graph, mutation_graph)
    return endpoint.dispatch({'query': query_str})['data']


def introspect(query_graph, mutation_graph=None):
    return execute(INTROSPECTION_QUERY, query_graph, mutation_graph)


def test_introspection_query():
    @schema_directive(
        name='custom',
        locations=[Location.FIELD_DEFINITION],
    )
    class Custom(SchemaDirective):
        ...

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
            Field('_cowered', String, _noop),
            Field('entero', Float, _noop),
            Field('oldField', Float, _noop,
                  directives=[Deprecated('obsolete')]),
            Link('oldLink', Sequence[TypeRef['decian']], _noop, requires=None,
                 directives=[Deprecated('obsolete link')]),
            Link('toma', Sequence[TypeRef['decian']], _noop, requires=None),
        ]),
    ], directives=[Custom])
    assert introspect(graph) == _schema([
        _type('flexed', 'OBJECT', fields=[
            _field('yari', _non_null(_BOOL), args=[
                _ival('membuka', _seq_of(_STR), defaultValue='["frayed"]'),
                _ival('modist', _INT, defaultValue='null',
                      description='callow'),
            ]),
        ]),
        _type('decian', 'OBJECT', fields=[
            _field('dogme', _non_null(_INT)),
            _field('clarkia', _seq_of(_obj('flexed'))),
        ]),
        _type('Query', 'OBJECT', fields=[
            _field('entero', _non_null(_FLOAT)),
            _field(
                'oldField',
                _non_null(_FLOAT),
                isDeprecated=True,
                deprecationReason='obsolete',
            ),
            _field(
                'oldLink',
                _seq_of(_obj('decian')),
                isDeprecated=True,
                deprecationReason='obsolete link',
            ),
            _field('toma', _seq_of(_obj('decian'))),
        ]),
    ], [
        _directive('custom', ['FIELD_DEFINITION']),
    ])


def test_invalid_names():
    graph = Graph([
        Node('Baz-Baz', [
            Field('bzz-bzz', Integer, _noop),
        ]),
        Root([
            Field('foo-foo', Integer, _noop,
                  options=[Option('bar-bar', Integer)]),
            Link('baz-baz', Sequence[TypeRef['Baz-Baz']], _noop,
                 requires='foo-foo'),
        ]),
    ])
    with pytest.raises(ValueError) as err:
        apply(graph, [GraphQLIntrospection(graph)])
    assert err.match('bzz-bzz')
    assert err.match('foo-foo')
    assert err.match('bar-bar')
    assert err.match('baz-baz')
    assert err.match('Baz-Baz')


def test_empty_nodes():
    graph = Graph([
        Node('Foo', []),
        Root([]),
    ])
    with pytest.raises(ValueError) as err:
        apply(graph, [GraphQLIntrospection(graph)])
    assert err.match('No fields in the Foo node')
    assert err.match('No fields in the Root node')


def test_unsupported_field_type():
    graph = Graph([
        Root([
            Field('fall', Optional[Any], _noop),
            Field('bayman', Optional[Record[{'foo': Optional[Integer]}]],
                  _noop),
            Field('huss', Integer, _noop),
        ]),
    ])
    assert introspect(graph) == _schema([
        _type('Query', 'OBJECT', fields=[
            _field('fall', _ANY),
            _field('bayman', _ANY),
            _field('huss', _non_null(_INT)),
        ]),
    ])


def test_unsupported_option_type():
    graph = Graph([
        Root([
            Field('huke', Integer, _noop,
                  options=[Option('orel', Optional[Any])]),
            Field('terapin', Integer, _noop),
        ]),
    ])
    assert introspect(graph) == _schema([
        _type('Query', 'OBJECT', fields=[
            _field('huke', _non_null(_INT), args=[
                _ival('orel', _ANY),
            ]),
            _field('terapin', _non_null(_INT)),
        ]),
    ])


def test_data_types():
    data_types = {
        'Foo': Record[{
            'bar': Integer,
        }],
    }
    graph = Graph([Root([
        Field('foo', TypeRef['Foo'], _noop),
    ])], data_types)
    assert introspect(graph) == _schema([
        _type('Query', 'OBJECT', fields=[
            _field('foo', _non_null(_obj('Foo'))),
        ]),
        _type('Foo', 'OBJECT', fields=[
            _field('bar', _non_null(_INT)),
        ]),
        _type('IOFoo', 'INPUT_OBJECT', inputFields=[
            _ival('bar', _non_null(_INT)),
        ]),
    ])


def test_mutation_type():
    data_types = {
        'Foo': Record[{
            'bar': Integer,
        }],
    }
    query_graph = Graph([Root([
        Field('getFoo', Integer, _noop, options=[
            Option('getterArg', TypeRef['Foo']),
        ]),
    ])], data_types)
    mutation_graph = Graph(query_graph.nodes + [Root([
        Field('setFoo', Integer, _noop, options=[
            Option('setterArg', TypeRef['Foo']),
        ]),
    ])], data_types=query_graph.data_types)
    assert introspect(query_graph, mutation_graph) == _schema([
        _type('Query', 'OBJECT', fields=[
            _field('getFoo', _non_null(_INT), args=[
                _ival('getterArg', _non_null(_iobj('IOFoo'))),
            ]),
        ]),
        _type('Mutation', 'OBJECT', fields=[
            _field('setFoo', _non_null(_INT), args=[
                _ival('setterArg', _non_null(_iobj('IOFoo'))),
            ]),
        ]),
        _type('Foo', 'OBJECT', fields=[
            _field('bar', _non_null(_INT)),
        ]),
        _type('IOFoo', 'INPUT_OBJECT', inputFields=[
            _ival('bar', _non_null(_INT)),
        ]),
    ], with_mutation=True)


def test_untyped_fields():
    graph = Graph([
        Root([
            Field('untyped', None, _noop),
            Field('any_typed', Any, _noop),
        ]),
    ])
    assert introspect(graph) == _schema([
        _type('Query', 'OBJECT', fields=[
            _field('untyped', _ANY),
            _field('any_typed', _ANY),
        ]),
    ])


def test_unions():
    graph = Graph([
        Node('Audio', [
            Field('id', Integer, _noop),
            Field('duration', String, _noop),
        ]),
        Node('Video', [
            Field('id', Integer, _noop),
            Field('thumbnailUrl', String, _noop),
        ]),
        Root([
            Link('mediaList', Sequence[UnionRef['Media']], _noop, requires=None),
            Link('mediaOne', UnionRef['Media'], _noop, requires=None),
            Link('maybeMedia', Optional[UnionRef['Media']], _noop, requires=None),
        ]),
    ], unions=[
        Union('Media', ['Audio', 'Video']),
    ])

    assert introspect(graph) == _schema([
        _type('Audio', 'OBJECT', fields=[
            _field('id', _non_null(_INT)),
            _field('duration', _non_null(_STR)),
        ]),
        _type('Video', 'OBJECT', fields=[
            _field('id', _non_null(_INT)),
            _field('thumbnailUrl', _non_null(_STR)),
        ]),
        _type('Query', 'OBJECT', fields=[
            _field('mediaList', _seq_of(_union('Media'))),
            _field('mediaOne', _non_null(_union('Media'))),
            _field('maybeMedia', _union('Media')),
        ]),
        _type('Media', 'UNION', possibleTypes=[
            _obj('Audio'),
            _obj('Video'),
        ]),
    ])


def test_interfaces():
    graph = Graph([
        Node('Audio', [
            Field('id', Integer, _noop),
            Field('duration', String, _noop),
            Field('album', String, _noop),
        ], implements=['Media']),
        Node('Video', [
            Field('id', Integer, _noop),
            Field('duration', String, _noop),
            Field('thumbnailUrl', String, _noop),
        ], implements=['Media']),
        Root([
            Link('media', InterfaceRef['Media'], _noop, requires=None),
            Link('mediaList', Sequence[InterfaceRef['Media']], _noop, requires=None),
            Link('maybeMedia', Optional[InterfaceRef['Media']], _noop, requires=None),
        ]),
    ], interfaces=[
        Interface('Media', [
            Field('id', Integer, _noop),
            Field('duration', String, _noop),
        ]),
    ])

    assert introspect(graph) == _schema([
        _type('Audio', 'OBJECT', fields=[
            _field('id', _non_null(_INT)),
            _field('duration', _non_null(_STR)),
            _field('album', _non_null(_STR)),
        ], interfaces=[_interface('Media')]),
        _type('Video', 'OBJECT', fields=[
            _field('id', _non_null(_INT)),
            _field('duration', _non_null(_STR)),
            _field('thumbnailUrl', _non_null(_STR)),
        ], interfaces=[_interface('Media')]),
        _type('Query', 'OBJECT', fields=[
            _field('media', _non_null(_interface('Media'))),
            _field('mediaList', _seq_of(_interface('Media'))),
            _field('maybeMedia', _interface('Media')),
        ]),
        _type('Media', 'INTERFACE', possibleTypes=[
            _obj('Audio'),
            _obj('Video'),
        ], fields=[
            _field('id', _non_null(_INT)),
            _field('duration', _non_null(_STR)),
        ]),
    ])


def test_enum():
    class Status(enum.Enum):
        ACTIVE = 'ACTIVE'
        DELETED = 'DELETED'

    graph = Graph([
        Node('User', [
            Field('id', Integer, _noop),
            Field('status', EnumRef['UserStatus'], _noop),
        ]),
        Root([
            Link(
                'user',
                Optional[TypeRef['User']],
                _noop,
                requires=None,
                options=[
                    Option('status', EnumRef['UserStatus'], default=Status.ACTIVE)
                ]
            ),
        ]),
    ], enums=[Enum.from_builtin(Status, 'UserStatus')])

    assert introspect(graph) == _schema([
        _type('User', 'OBJECT', fields=[
            _field('id', _non_null(_INT)),
            _field('status', _non_null(_enum('UserStatus'))),
        ]),
        _type('Query', 'OBJECT', fields=[
            _field('user', _obj('User'), args=[
                _ival('status', _non_null(_enum('UserStatus')), defaultValue='ACTIVE'),
            ]),
        ]),
        _type('UserStatus', 'ENUM', enumValues=[
            _enum_value('ACTIVE'),
            _enum_value('DELETED'),
        ]),
    ])


@pytest.mark.parametrize('enum_name, expected', [
    ('Status', {'kind': 'ENUM', "enumValues": [{"name": "ACTIVE"}, {"name": "DELETED"}]}),
    ('XXX', None),
])
def test_query_enum_as_single_type(enum_name, expected):
    query = """
    query IntrospectionQuery {
        __type(name: "%s") {
            kind
            enumValues {
                name
            }
       }
    }
    """ % enum_name

    class Status(enum.Enum):
        ACTIVE = 'ACTIVE'
        DELETED = 'DELETED'

    graph = Graph([
        Root([
            Field('status', EnumRef['Status'], _noop),
        ]),
    ], enums=[Enum.from_builtin(Status)])

    got = execute(query, graph)
    assert got['__type'] == expected


def test_custom_scalar():
    class UserId(Scalar):
        @classmethod
        def parse(cls, value: str) -> int:
            return int(value[3:])

        @classmethod
        def serialize(cls, value: int) -> str:
            return 'uid%d' % value

    graph = Graph([
        Node('User', [
            Field('id', Integer, _noop),
            Field('uid', UserId, _noop),
        ]),
        Root([
            Link(
                'user',
                Optional[TypeRef['User']],
                _noop,
                requires=None,
                options=[
                    Option('uid', UserId, default=1),
                    Option('uidMany', Sequence[UserId], default=[1]),
                    Option('uidMaybe', Optional[UserId], default=None)
                ]
            ),
        ]),
    ], scalars=[UserId])

    assert _schema([
        _type(
            'User',
            'OBJECT',
            fields=[
                _field('id', _non_null(_INT)),
                _field('uid', _non_null(_scalar('UserId'))),
            ],

        ),
        _type('Query', 'OBJECT', fields=[
            _field('user', _obj('User'), args=[
                _ival('uid', _non_null(_scalar('UserId')), defaultValue='uid1'),
                _ival('uidMany', _seq_of(_scalar('UserId')), defaultValue=['uid1']),
                _ival('uidMaybe', _scalar('UserId'), defaultValue=None),
            ]),
        ], ),
        _type('UserId', 'SCALAR'),
    ]) == introspect(graph)

@pytest.mark.parametrize('name, expected', [
    ('YesNo', {'kind': 'SCALAR'}),
    ('XXX', None),
])
def test_query_scalar_as_single_type(name, expected):
    query = """
    query IntrospectionQuery {
        __type(name: "%s") {
            kind
       }
    }
    """ % name

    class YesNo(Scalar):
        @classmethod
        def parse(cls, value: str) -> bool:
            return value == 'yes'

        @classmethod
        def serialize(cls, value: bool) -> str:
            return 'yes' if value else 'no'

    graph = Graph([
        Root([
            Field('status', YesNo, _noop),
        ]),
    ], scalars=[YesNo])

    got = execute(query, graph)
    assert got['__type'] == expected
