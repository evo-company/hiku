from federation.directive import (
    KeyDirective,
    RequiresDirective,
    ProvidesDirective,
    ExternalDirective
)
from hiku.introspection.graphql import (
    GraphQLIntrospection,
    AsyncGraphQLIntrospection,
)


def is_introspection_query(query):
    return '__schema' in query.fields_map


_ANY_FEDERATED = {'kind': 'SCALAR', 'name': '_Any', 'ofType': None}


def _obj(name):
    return {'kind': 'OBJECT', 'name': name, 'ofType': None}


def _union(name, possible_types=None):
    return {
        'kind': 'UNION',
        'name': name,
        'possibleTypes': possible_types
    }


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


def _seq_of(_type):
    return {'kind': 'NON_NULL', 'name': None,
            'ofType': {'kind': 'LIST', 'name': None,
                       'ofType': {'kind': 'NON_NULL', 'name': None,
                                  'ofType': _type}}}


def _seq_of_nullable(_type):
    return {'kind': 'NON_NULL', 'name': None,
            'ofType': {'kind': 'LIST', 'name': None,
                       'ofType': _type}}


def _ival(name, type_, **kwargs):
    data = {
        'name': name,
        'type': type_,
        'description': None,
        'defaultValue': None,
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


def extend_with_federation(data: dict):
    data['__schema']['types'].append(_type('_Any', 'SCALAR'))

    for t in data['__schema']['types']:
        if t['kind'] == 'OBJECT' and t['name'] == 'Query':
            t['fields'].append(
                _field(
                    '_entities',
                    _seq_of_nullable(_union('_Entity', [_obj('Astronaut')])),
                    args=[_ival('representations', _seq_of(_ANY_FEDERATED))]
                )
            )


class FederatedGraphQLIntrospection(GraphQLIntrospection):
    """
    Federation-aware introspection
    https://www.apollographql.com/docs/federation/federation-spec/#federation-schema-specification
    """
    def __init__(self, query_graph, mutation_graph=None, directives=None, scalars=None):
        if not directives:
            directives = []

        directives.extend([
            KeyDirective(),
            RequiresDirective(),
            ProvidesDirective(),
            ExternalDirective()
        ])

        super().__init__(query_graph, mutation_graph, directives, scalars)


class AsyncFederatedGraphQLIntrospection(
    FederatedGraphQLIntrospection,
    AsyncGraphQLIntrospection
):
    """Adds GraphQL introspection into asynchronous federated graph"""
