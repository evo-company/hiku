from unittest.mock import ANY

from federation.directive import (
    KeyDirective,
    RequiresDirective,
    ExternalDirective,
    ProvidesDirective,
)
from federation.graph import (
    FederatedGraph,
    ExtendNode,
    ExtendLink,
)
from federation.introspection import FederatedGraphQLIntrospection
from hiku.graph import Root, Field, Node, Link, apply, Option
from hiku.introspection.directive import (
    Directive,
    SkipDirective,
    IncludeDirective,
)
from hiku.introspection.types import (
    NON_NULL,
    SCALAR,
)
from hiku.types import String, Integer, Sequence, TypeRef, Boolean, Float, Any
from hiku.types import Optional, Record
from hiku.result import denormalize
from hiku.engine import Engine
from hiku.executors.sync import SyncExecutor
from hiku.validate.query import validate
from hiku.readers.graphql import read


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
_ANY = {'kind': 'SCALAR', 'name': 'Any', 'ofType': None}
_ANY_FEDERATED = {'kind': 'SCALAR', 'name': '_Any', 'ofType': None}


def _obj(name):
    return {'kind': 'OBJECT', 'name': name, 'ofType': None}


def _iobj(name):
    return {'kind': 'INPUT_OBJECT', 'name': name, 'ofType': None}


def _union(name, possible_types = None):
    union = {
        'kind': 'UNION',
        'name': name,
    }

    if possible_types:
        union["possibleTypes"] = possible_types
    else:
        union["ofType"] = None

    return union

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


def _directive(directive: Directive):
    args = []
    for arg_name, arg in directive.args.items():
        if arg.type == NON_NULL(SCALAR('Boolean')):
            args.append(_ival(arg_name, _non_null(_BOOL), description=ANY))
        elif arg.type == NON_NULL(SCALAR('String')):
            args.append(_ival(arg_name, _non_null(_STR), description=ANY))

    return {
        'name': directive.name,
        'description': directive.description,
        "locations": directive.locations,
        "args": args,
    }


def _schema(types, with_mutation=False):
    names = [t['name'] for t in types]
    assert 'Query' in names, names
    return {
        '__schema': {
            'directives': [
                _directive(SkipDirective()),
                _directive(IncludeDirective()),
                _directive(KeyDirective()),
                _directive(RequiresDirective()),
                _directive(ProvidesDirective()),
                _directive(ExternalDirective()),
            ],
            'mutationType': {'name': 'Mutation'} if with_mutation else None,
            'queryType': {'name': 'Query'},
            'types': SCALARS + types,
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
    _type('_Any', 'SCALAR'),
]


def introspect(query_graph, mutation_graph=None):
    engine = Engine(SyncExecutor())
    query_graph = apply(query_graph, [
        FederatedGraphQLIntrospection(query_graph, mutation_graph),
    ])

    query = read(QUERY)
    errors = validate(query_graph, query)
    assert not errors

    norm_result = engine.execute(query_graph, query)
    return denormalize(query_graph, norm_result)


AstronautNode = ExtendNode('Astronaut', [
    Field('id', Integer, _noop),
    Field('name', String, _noop),
    Field('age', Integer, _noop),
], keys=['id'])


AstronautsLink = ExtendLink(
    'astronauts',
    Sequence[TypeRef['Astronaut']],
    _noop,
    requires=None,
    options=None,
)

ROOT_FIELDS = [
    AstronautsLink,
]


def test_federated_introspection_query_directives():
    graph = FederatedGraph([
        AstronautNode,
        Root(ROOT_FIELDS),
    ])

    exp = _schema([
        _type('Astronaut', 'OBJECT', fields=[
            _field('id', _non_null(_INT)),
            _field('name', _non_null(_STR)),
            _field('age', _non_null(_INT)),
        ]),
        _type('Query', 'OBJECT', fields=[
            _field('astronauts', _seq_of(_obj('Astronaut'))),
        ]),
    ])
    assert exp == introspect(graph)


def test_federated_introspection_query_entities():
    graph = FederatedGraph([
        AstronautNode,
        Root(ROOT_FIELDS),
    ])

    exp = _schema([
        _type('Astronaut', 'OBJECT', fields=[
            _field('id', _non_null(_INT)),
            _field('name', _non_null(_STR)),
            _field('age', _non_null(_INT)),
        ]),
        _type('Query', 'OBJECT', fields=[
            _field('astronauts', _seq_of(_obj('Astronaut'))),
            _field(
                '_entities',
                # _seq_of_nullable(_union('_Entity', [_obj('Astronaut')])),
                _seq_of_nullable(_union('_Entity')),
                args=[
                    _ival(
                        'representations',
                        _seq_of(_ANY_FEDERATED),
                        defaultValue='null'
                    ),
                ]
            ),
        ]),
    ])
    got = introspect(graph)
    assert exp == got


def test_federated_introspection_query_service():
    pass
