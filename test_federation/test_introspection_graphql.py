from unittest.mock import ANY

from federation.directive import (
    KeyDirective,
    RequiresDirective,
    ExternalDirective,
    ProvidesDirective,
)
from federation.graph import FederatedGraph
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


def _obj(name):
    return {'kind': 'OBJECT', 'name': name, 'ofType': None}


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


def test_federated_introspection_query_directives():
    graph = FederatedGraph([
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
            Link('toma', Sequence[TypeRef['decian']], _noop, requires=None),
        ]),
    ])
    exp = _schema([
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
            _field('toma', _seq_of(_obj('decian'))),
        ]),
    ])
    assert exp == introspect(graph)


def test_federated_introspection_query_Entities():
    pass


def test_federated_introspection_query_Service():
    pass
