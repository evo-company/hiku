from .directive import (
    Key,
    Requires,
    Provides,
    External
)
from hiku.graph import Graph
from hiku.introspection.graphql import (
    GraphQLIntrospection,
    AsyncGraphQLIntrospection,
)


def is_introspection_query(query):
    return '__schema' in query.fields_map


def _obj(name):
    return {'kind': 'OBJECT', 'name': name, 'ofType': None}


def _non_null(t):
    return {'kind': 'NON_NULL', 'name': None, 'ofType': t}


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


def _seq_of_nullable(_type):
    return {'kind': 'NON_NULL', 'name': None,
            'ofType': {'kind': 'LIST', 'name': None,
                       'ofType': _type}}


def _seq_of(_type):
    return _seq_of_nullable({'kind': 'NON_NULL', 'name': None,
                            'ofType': _type})


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


def extend_with_federation(graph: Graph, data: dict):
    union_types = []
    for node in graph.nodes:
        if 'key' in node.directives_map:
            union_types.append(_obj(node.name))

    data['__schema']['types'].append(_type('_Any', 'SCALAR'))
    data['__schema']['types'].append(
        _type('_Entity', 'UNION', possibleTypes=union_types)
    )
    data['__schema']['types'].append(
        _type('_Service', 'OBJECT',
              fields=[_field('sdl', _type('String', 'SCALAR'))])
    )

    entities_field = _field(
        '_entities',
        _seq_of_nullable(_union('_Entity', union_types)),
        args=[_ival('representations', _seq_of(_type('_Any', 'SCALAR')))]
    )

    service_field = _field(
        '_service',
        _non_null(_obj('_Service')),
    )
    for t in data['__schema']['types']:
        if t['kind'] == 'OBJECT' and t['name'] == 'Query':
            t['fields'].append(entities_field)
            t['fields'].append(service_field)


class FederatedGraphQLIntrospection(GraphQLIntrospection):
    """
    Federation-aware introspection
    https://www.apollographql.com/docs/federation/federation-spec/#federation-schema-specification
    """
    def __init__(self, query_graph, mutation_graph=None, directives=None):
        if not directives:
            directives = []

        directives.extend([
            Key(),
            Requires(),
            Provides(),
            External()
        ])

        super().__init__(query_graph, mutation_graph, directives)


class AsyncFederatedGraphQLIntrospection(
    FederatedGraphQLIntrospection,
    AsyncGraphQLIntrospection
):
    """Adds GraphQL introspection into asynchronous federated graph"""
